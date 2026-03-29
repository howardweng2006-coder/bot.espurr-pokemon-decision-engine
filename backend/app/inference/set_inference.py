from __future__ import annotations

from app.domain.battle_state import BattleState, PokemonState
from app.inference.models import CandidateSet, InferenceResult


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

    placeholder_candidate = CandidateSet(
        species=species,
        label="generic-placeholder-set",
        moves=list(pokemon.revealed_moves),
        weight=1.0,
        source="placeholder",
    )

    notes = [
        "Inference layer is currently a placeholder.",
        "No metagame priors are loaded yet.",
        "Revealed moves are preserved when present, but no real filtering is applied yet.",
    ]

    return InferenceResult(
        species=species,
        candidates=[placeholder_candidate],
        confidence_label="placeholder",
        notes=notes,
    )