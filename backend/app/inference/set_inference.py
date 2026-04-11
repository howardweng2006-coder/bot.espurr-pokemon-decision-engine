from __future__ import annotations

from app.domain.battle_state import BattleState, PokemonState
from app.inference.candidate_builder import CandidateBuildInput, CandidateBuilder
from app.inference.models import CandidateBuilderConfig, CandidateSet, InferenceResult
from app.providers.meta_provider import MetaProvider, MetaQuery


SPECIES_DEFAULT_ABILITY: dict[str, str] = {
    "Rotom-Wash": "Levitate",
    "Rotom-Heat": "Levitate",
    "Rotom-Mow": "Levitate",
    "Rotom-Frost": "Levitate",
    "Rotom-Fan": "Levitate",
    "Rotom": "Levitate",
    "Weezing": "Levitate",
}

SPECIES_FALLBACK_MOVES: dict[str, list[str]] = {
    "Rotom-Wash": ["Hydro Pump", "Volt Switch", "Will-O-Wisp", "Pain Split"],
}


DEFAULT_META_QUERY = MetaQuery(
    format_id="gen9ou",
    generation=9,
    rating_bucket="1695",
    month_window=3,
)


def _merge_revealed_moves(base_moves: list[str], revealed_moves: list[str]) -> list[str]:
    merged = list(base_moves)
    for revealed_move in revealed_moves:
        if revealed_move not in merged:
            merged.append(revealed_move)
    return merged


def _build_species_fallback_candidate(pokemon: PokemonState) -> CandidateSet | None:
    species = pokemon.species
    if not species:
        return None

    ability = SPECIES_DEFAULT_ABILITY.get(species)
    fallback_moves = SPECIES_FALLBACK_MOVES.get(species, [])
    merged_moves = _merge_revealed_moves(fallback_moves, list(pokemon.revealed_moves))

    if ability is None and not merged_moves:
        return None

    confirmed_moves = list(pokemon.revealed_moves)
    assumed_moves = [move for move in merged_moves if move not in confirmed_moves]

    return CandidateSet(
        species=species,
        label="species-fallback-set",
        moves=merged_moves,
        ability=ability,
        prior_weight=1.0,
        compatibility_weight=1.0,
        evidence_weight=1.0,
        final_weight=1.0,
        source="species-fallback",
        confirmed_moves=confirmed_moves,
        assumed_moves=assumed_moves,
        notes=["Species fallback candidate used after provider lookup missed."],
    )


def _build_placeholder_candidate(pokemon: PokemonState) -> CandidateSet:
    species = pokemon.species or "Unknown"
    confirmed_moves = list(pokemon.revealed_moves)

    return CandidateSet(
        species=species,
        label="generic-placeholder-set",
        moves=confirmed_moves,
        prior_weight=1.0,
        compatibility_weight=1.0,
        evidence_weight=1.0,
        final_weight=1.0,
        source="placeholder",
        confirmed_moves=confirmed_moves,
        assumed_moves=[],
        notes=["Placeholder candidate preserves only currently revealed information."],
    )


def _normalize_candidates(candidates: list[CandidateSet]) -> list[CandidateSet]:
    viable = [candidate for candidate in candidates if not candidate.is_eliminated]
    total = sum(max(0.0, candidate.final_weight) for candidate in viable) or 1.0

    normalized: list[CandidateSet] = []
    for candidate in candidates:
        final_weight = 0.0 if candidate.is_eliminated else max(0.0, candidate.final_weight) / total
        normalized.append(
            CandidateSet(
                species=candidate.species,
                label=candidate.label,
                moves=list(candidate.moves),
                item=candidate.item,
                ability=candidate.ability,
                tera_type=candidate.tera_type,
                spread_label=candidate.spread_label,
                nature=candidate.nature,
                evs=dict(candidate.evs),
                ivs=dict(candidate.ivs),
                prior_weight=candidate.prior_weight,
                compatibility_weight=candidate.compatibility_weight,
                evidence_weight=candidate.evidence_weight,
                final_weight=final_weight,
                source=candidate.source,
                confirmed_moves=list(candidate.confirmed_moves),
                assumed_moves=list(candidate.assumed_moves),
                notes=list(candidate.notes),
                penalties=list(candidate.penalties),
                elimination_reasons=list(candidate.elimination_reasons),
            )
        )

    return normalized


def _build_from_provider(
    pokemon: PokemonState,
    *,
    meta_provider: MetaProvider,
    candidate_builder: CandidateBuilder,
    query: MetaQuery,
) -> InferenceResult | None:
    species = pokemon.species
    if not species:
        return None

    species_prior = meta_provider.get_species_prior(query, species)
    if species_prior is None:
        return None

    built_candidates = candidate_builder.build(
        CandidateBuildInput(
            species=species,
            prior=species_prior,
            revealed_moves=list(pokemon.revealed_moves),
        )
    )

    if not built_candidates:
        return None

    normalized = _normalize_candidates(built_candidates)
    return InferenceResult(
        species=species,
        candidates=normalized,
        confidence_label="provider-backed",
        notes=[
            f"Provider-backed priors loaded for {species}.",
            f"Format={query.format_id}, gen={query.generation}, rating={query.rating_bucket}, months={query.month_window}.",
            "Candidate builder constructed plausible sets from normalized species priors.",
            "Revealed moves were incorporated during candidate construction.",
        ],
    )


def _build_from_species_fallback(pokemon: PokemonState) -> InferenceResult | None:
    species = pokemon.species
    if not species:
        return None

    fallback_candidate = _build_species_fallback_candidate(pokemon)
    if fallback_candidate is None:
        return None

    return InferenceResult(
        species=species,
        candidates=[fallback_candidate],
        confidence_label="species-fallback",
        notes=[
            f"No provider-backed priors found for {species}.",
            "Used species-aware fallback candidate for basic competitive realism.",
            "Fallback preserves revealed moves and injects only high-impact deterministic assumptions.",
        ],
    )


def infer_opposing_active_set(
    state: BattleState,
    *,
    meta_provider: MetaProvider | None = None,
    candidate_builder: CandidateBuilder | None = None,
) -> InferenceResult:
    return infer_pokemon_state(
        state.opponent_side.active,
        meta_provider=meta_provider,
        candidate_builder=candidate_builder,
    )


def infer_pokemon_state(
    pokemon: PokemonState,
    *,
    meta_provider: MetaProvider | None = None,
    candidate_builder: CandidateBuilder | None = None,
    query: MetaQuery = DEFAULT_META_QUERY,
) -> InferenceResult:
    species = pokemon.species

    if not species:
        return InferenceResult(
            species=None,
            candidates=[],
            confidence_label="unknown",
            notes=["No species provided, so no candidate sets were generated."],
        )

    builder = candidate_builder or CandidateBuilder(CandidateBuilderConfig())

    if meta_provider is not None:
        provider_result = _build_from_provider(
            pokemon,
            meta_provider=meta_provider,
            candidate_builder=builder,
            query=query,
        )
        if provider_result is not None:
            return provider_result

    species_fallback_result = _build_from_species_fallback(pokemon)
    if species_fallback_result is not None:
        return species_fallback_result

    placeholder_candidate = _build_placeholder_candidate(pokemon)
    return InferenceResult(
        species=species,
        candidates=[placeholder_candidate],
        confidence_label="placeholder",
        notes=[
            f"No priors found for {species}.",
            "Placeholder candidate preserves revealed moves only.",
            "Provider data is missing for this species and no species fallback applied.",
        ],
    )