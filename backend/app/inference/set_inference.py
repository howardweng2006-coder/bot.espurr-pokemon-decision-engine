from __future__ import annotations

from app.domain.battle_state import BattleState, PokemonState
from app.inference.models import CandidateSet, InferenceResult


# First-pass local seeds.
# Replace later with a provider-backed meta snapshot.
SEEDED_OPPONENT_PRIORS: dict[str, list[CandidateSet]] = {
    "Great Tusk": [
        CandidateSet(
            species="Great Tusk",
            label="bulky-utility",
            moves=["Headlong Rush", "Earthquake", "Knock Off", "Rapid Spin", "Stealth Rock"],
            item="Leftovers",
            ability="Protosynthesis",
            weight=0.50,
            source="seed",
        ),
        CandidateSet(
            species="Great Tusk",
            label="offensive-spinner",
            moves=["Headlong Rush", "Close Combat", "Ice Spinner", "Rapid Spin"],
            item="Booster Energy",
            ability="Protosynthesis",
            weight=0.30,
            source="seed",
        ),
        CandidateSet(
            species="Great Tusk",
            label="scarf-attacker",
            moves=["Earthquake", "Close Combat", "Knock Off", "Ice Spinner"],
            item="Choice Scarf",
            ability="Protosynthesis",
            weight=0.20,
            source="seed",
        ),
    ],
    "Kingambit": [
        CandidateSet(
            species="Kingambit",
            label="black-glasses-sd",
            moves=["Kowtow Cleave", "Sucker Punch", "Iron Head", "Swords Dance"],
            item="Black Glasses",
            ability="Supreme Overlord",
            weight=0.45,
            source="seed",
        ),
        CandidateSet(
            species="Kingambit",
            label="leftovers-bulky",
            moves=["Kowtow Cleave", "Sucker Punch", "Iron Head", "Low Kick"],
            item="Leftovers",
            ability="Supreme Overlord",
            weight=0.30,
            source="seed",
        ),
        CandidateSet(
            species="Kingambit",
            label="banded-attacker",
            moves=["Kowtow Cleave", "Sucker Punch", "Iron Head", "Low Kick"],
            item="Choice Band",
            ability="Supreme Overlord",
            weight=0.25,
            source="seed",
        ),
    ],
}

# Small species-aware fallback layer for high-impact competitive realism.
# This is intentionally tiny and should later be replaced by provider-backed priors.
SPECIES_DEFAULT_ABILITY: dict[str, str] = {
    "Rotom-Wash": "Levitate",
    "Rotom-Heat": "Levitate",
    "Rotom-Mow": "Levitate",
    "Rotom-Frost": "Levitate",
    "Rotom-Fan": "Levitate",
    "Rotom": "Levitate",
    "Weezing": "Levitate",
    "Hydreigon": "Levitate",  # example of why this table should stay curated; delete if wrong
}

# Keep this very small. The goal is not to simulate the metagame yet.
SPECIES_FALLBACK_MOVES: dict[str, list[str]] = {
    "Rotom-Wash": ["Hydro Pump", "Volt Switch", "Will-O-Wisp", "Pain Split"],
}

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

    return CandidateSet(
        species=species,
        label="species-fallback-set",
        moves=merged_moves,
        ability=ability,
        weight=1.0,
        source="species-fallback",
    )


def infer_opposing_active_set(state: BattleState) -> InferenceResult:
    opposing_active = state.opponent_side.active
    return infer_pokemon_state(opposing_active)


def infer_pokemon_state(pokemon: PokemonState) -> InferenceResult:
    species = pokemon.species

    if not species:
        return InferenceResult(
            species=None,
            candidates=[],
            confidence_label="unknown",
            notes=[
                "No species provided, so no candidate sets were generated.",
            ],
        )

    seeded = SEEDED_OPPONENT_PRIORS.get(species)
    if not seeded:
        fallback_candidate = _build_species_fallback_candidate(pokemon)
        if fallback_candidate is not None:
            return InferenceResult(
                species=species,
                candidates=[fallback_candidate],
                confidence_label="species-fallback",
                notes=[
                    f"No seeded priors found for {species}.",
                    "Used species-aware fallback candidate for basic competitive realism.",
                    "Fallback preserves revealed moves and injects only high-impact deterministic assumptions.",
                ],
            )

        placeholder_candidate = CandidateSet(
            species=species,
            label="generic-placeholder-set",
            moves=list(pokemon.revealed_moves),
            weight=1.0,
            source="placeholder",
        )
        return InferenceResult(
            species=species,
            candidates=[placeholder_candidate],
            confidence_label="placeholder",
            notes=[
                "No seeded priors found for this species.",
                "Fallback candidate preserves revealed moves only.",
                "Meta-provider integration is not loaded yet.",
            ],
        )

    candidates: list[CandidateSet] = []
    for candidate in seeded:
        merged_moves = _merge_revealed_moves(candidate.moves, list(pokemon.revealed_moves))

        candidates.append(
            CandidateSet(
                species=candidate.species,
                label=candidate.label,
                moves=merged_moves,
                item=candidate.item,
                ability=candidate.ability,
                tera_type=candidate.tera_type,
                weight=candidate.weight,
                source=candidate.source,
            )
        )

    notes = [
        f"Seeded priors loaded for {species}.",
        "Revealed moves were merged into all plausible candidate sets.",
        "Weights are still seed-level and not yet updated dynamically from battle evidence.",
    ]

    return InferenceResult(
        species=species,
        candidates=candidates,
        confidence_label="seeded",
        notes=notes,
    )