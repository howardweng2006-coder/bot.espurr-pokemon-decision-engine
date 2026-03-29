from __future__ import annotations

from typing import Iterable

from app.inference.models import CandidateSet, InferenceResult


def renormalize_candidates(candidates: Iterable[CandidateSet]) -> list[CandidateSet]:
    candidates = list(candidates)
    total = sum(candidate.weight for candidate in candidates) or 1.0

    renormalized: list[CandidateSet] = []
    for candidate in candidates:
        renormalized.append(
            CandidateSet(
                species=candidate.species,
                label=candidate.label,
                moves=list(candidate.moves),
                item=candidate.item,
                ability=candidate.ability,
                tera_type=candidate.tera_type,
                weight=candidate.weight / total,
                source=candidate.source,
            )
        )

    return renormalized


def apply_revealed_move(
    inference: InferenceResult,
    revealed_move: str,
) -> InferenceResult:
    updated_candidates: list[CandidateSet] = []

    for candidate in inference.candidates:
        updated_moves = list(candidate.moves)
        if revealed_move not in updated_moves:
            updated_moves.append(revealed_move)

        updated_candidates.append(
            CandidateSet(
                species=candidate.species,
                label=candidate.label,
                moves=updated_moves,
                item=candidate.item,
                ability=candidate.ability,
                tera_type=candidate.tera_type,
                weight=candidate.weight,
                source=candidate.source,
            )
        )

    updated_candidates = renormalize_candidates(updated_candidates)

    updated_notes = list(inference.notes)
    updated_notes.append(
        f"Belief updater placeholder recorded revealed move: {revealed_move}."
    )

    return InferenceResult(
        species=inference.species,
        candidates=updated_candidates,
        confidence_label=inference.confidence_label,
        notes=updated_notes,
    )