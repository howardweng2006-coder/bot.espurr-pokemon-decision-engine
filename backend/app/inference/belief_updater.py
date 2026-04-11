from __future__ import annotations

from typing import Iterable, Optional

from app.inference.models import CandidateSet, InferenceResult, OpponentWorld


def _copy_candidate(
    candidate: CandidateSet,
    *,
    moves: list[str] | None = None,
    item: str | None = None,
    ability: str | None = None,
    tera_type: str | None = None,
    evidence_weight: float | None = None,
    final_weight: float | None = None,
    notes_append: list[str] | None = None,
    penalties_append: list[str] | None = None,
    elimination_reasons_append: list[str] | None = None,
) -> CandidateSet:
    next_moves = list(candidate.moves if moves is None else moves)
    confirmed_moves = [move for move in candidate.confirmed_moves if move in next_moves]
    assumed_moves = [move for move in next_moves if move not in confirmed_moves]

    next_notes = list(candidate.notes)
    if notes_append:
        next_notes.extend(notes_append)

    next_penalties = list(candidate.penalties)
    if penalties_append:
        next_penalties.extend(penalties_append)

    next_elimination_reasons = list(candidate.elimination_reasons)
    if elimination_reasons_append:
        next_elimination_reasons.extend(elimination_reasons_append)

    next_evidence_weight = candidate.evidence_weight if evidence_weight is None else evidence_weight
    next_final_weight = candidate.final_weight if final_weight is None else final_weight

    return CandidateSet(
        species=candidate.species,
        label=candidate.label,
        moves=next_moves,
        item=candidate.item if item is None else item,
        ability=candidate.ability if ability is None else ability,
        tera_type=candidate.tera_type if tera_type is None else tera_type,
        spread_label=candidate.spread_label,
        nature=candidate.nature,
        evs=dict(candidate.evs),
        ivs=dict(candidate.ivs),
        prior_weight=candidate.prior_weight,
        compatibility_weight=candidate.compatibility_weight,
        evidence_weight=next_evidence_weight,
        final_weight=next_final_weight,
        source=candidate.source,
        confirmed_moves=confirmed_moves,
        assumed_moves=assumed_moves,
        notes=next_notes,
        penalties=next_penalties,
        elimination_reasons=next_elimination_reasons,
    )


def renormalize_candidates(candidates: Iterable[CandidateSet]) -> list[CandidateSet]:
    candidates = list(candidates)
    viable = [candidate for candidate in candidates if not candidate.is_eliminated]
    total = sum(max(0.0, candidate.final_weight) for candidate in viable) or 1.0

    normalized: list[CandidateSet] = []
    for candidate in candidates:
        if candidate.is_eliminated:
            normalized_weight = 0.0
        else:
            normalized_weight = max(0.0, candidate.final_weight) / total

        normalized.append(
            _copy_candidate(
                candidate,
                final_weight=normalized_weight,
            )
        )

    return normalized


def _recompute_final_weight(candidate: CandidateSet, evidence_multiplier: float) -> float:
    if candidate.is_eliminated:
        return 0.0
    next_evidence_weight = candidate.evidence_weight * evidence_multiplier
    return candidate.prior_weight * candidate.compatibility_weight * next_evidence_weight


def apply_revealed_move(
    inference: InferenceResult,
    revealed_move: str,
) -> InferenceResult:
    updated_candidates: list[CandidateSet] = []

    for candidate in inference.candidates:
        updated_moves = list(candidate.moves)
        already_present = revealed_move in updated_moves
        if not already_present:
            updated_moves.append(revealed_move)

        updated_confirmed = list(candidate.confirmed_moves)
        if revealed_move not in updated_confirmed:
            updated_confirmed.append(revealed_move)

        evidence_multiplier = 1.35 if already_present else 0.90
        final_weight = _recompute_final_weight(candidate, evidence_multiplier)

        updated = _copy_candidate(
            candidate,
            moves=updated_moves,
            evidence_weight=candidate.evidence_weight * evidence_multiplier,
            final_weight=final_weight,
            notes_append=[f"Revealed move evidence applied: {revealed_move}."],
        )
        updated.confirmed_moves = updated_confirmed
        updated.assumed_moves = [move for move in updated.moves if move not in updated.confirmed_moves]
        updated_candidates.append(updated)

    updated_candidates = renormalize_candidates(updated_candidates)

    updated_notes = list(inference.notes)
    updated_notes.append(f"Belief updater recorded revealed move evidence: {revealed_move}.")

    return InferenceResult(
        species=inference.species,
        candidates=updated_candidates,
        confidence_label=inference.confidence_label,
        notes=updated_notes,
    )


def apply_item_evidence(
    inference: InferenceResult,
    item_name: str,
) -> InferenceResult:
    normalized_item = item_name.strip().lower()
    updated_candidates: list[CandidateSet] = []

    for candidate in inference.candidates:
        candidate_item = (candidate.item or "").strip().lower()

        if candidate_item == normalized_item:
            evidence_multiplier = 1.60
            next_item = candidate.item
            penalties: list[str] = []
        elif candidate_item:
            evidence_multiplier = 0.35
            next_item = candidate.item
            penalties = [f"Observed item {item_name} conflicts with assumed item {candidate.item}."]
        else:
            evidence_multiplier = 0.80
            next_item = item_name
            penalties = [f"Observed item {item_name} filled previously unknown item slot."]

        final_weight = _recompute_final_weight(candidate, evidence_multiplier)

        updated_candidates.append(
            _copy_candidate(
                candidate,
                item=next_item,
                evidence_weight=candidate.evidence_weight * evidence_multiplier,
                final_weight=final_weight,
                notes_append=[f"Item evidence applied: {item_name}."],
                penalties_append=penalties,
            )
        )

    updated_candidates = renormalize_candidates(updated_candidates)

    updated_notes = list(inference.notes)
    updated_notes.append(f"Belief updater recorded item evidence: {item_name}.")

    return InferenceResult(
        species=inference.species,
        candidates=updated_candidates,
        confidence_label=inference.confidence_label,
        notes=updated_notes,
    )


def apply_ability_evidence(
    inference: InferenceResult,
    ability_name: str,
) -> InferenceResult:
    normalized_ability = ability_name.strip().lower()
    updated_candidates: list[CandidateSet] = []

    for candidate in inference.candidates:
        candidate_ability = (candidate.ability or "").strip().lower()

        if candidate_ability == normalized_ability:
            evidence_multiplier = 1.60
            next_ability = candidate.ability
            penalties: list[str] = []
        elif candidate_ability:
            evidence_multiplier = 0.35
            next_ability = candidate.ability
            penalties = [f"Observed ability {ability_name} conflicts with assumed ability {candidate.ability}."]
        else:
            evidence_multiplier = 0.80
            next_ability = ability_name
            penalties = [f"Observed ability {ability_name} filled previously unknown ability slot."]

        final_weight = _recompute_final_weight(candidate, evidence_multiplier)

        updated_candidates.append(
            _copy_candidate(
                candidate,
                ability=next_ability,
                evidence_weight=candidate.evidence_weight * evidence_multiplier,
                final_weight=final_weight,
                notes_append=[f"Ability evidence applied: {ability_name}."],
                penalties_append=penalties,
            )
        )

    updated_candidates = renormalize_candidates(updated_candidates)

    updated_notes = list(inference.notes)
    updated_notes.append(f"Belief updater recorded ability evidence: {ability_name}.")

    return InferenceResult(
        species=inference.species,
        candidates=updated_candidates,
        confidence_label=inference.confidence_label,
        notes=updated_notes,
    )


def apply_branch_evidence(
    inference: InferenceResult,
    *,
    revealed_move: Optional[str] = None,
    item_evidence: Optional[str] = None,
    ability_evidence: Optional[str] = None,
) -> InferenceResult:
    updated = inference

    if revealed_move:
        updated = apply_revealed_move(updated, revealed_move)
    if item_evidence:
        updated = apply_item_evidence(updated, item_evidence)
    if ability_evidence:
        updated = apply_ability_evidence(updated, ability_evidence)

    updated_notes = list(updated.notes)
    updated_notes.append("Branch evidence was applied to the followup opponent belief state.")

    return InferenceResult(
        species=updated.species,
        candidates=updated.candidates,
        confidence_label=updated.confidence_label,
        notes=updated_notes,
    )


def worlds_to_inference(worlds: list[OpponentWorld]) -> InferenceResult:
    if not worlds:
        return InferenceResult(
            species=None,
            candidates=[],
            confidence_label="empty",
            notes=["No worlds were available for belief conversion."],
        )

    candidates: list[CandidateSet] = []
    for world in worlds:
        base = world.candidate
        assumed_item = world.assumed_item if world.assumed_item is not None else base.item
        assumed_ability = world.assumed_ability if world.assumed_ability is not None else base.ability
        assumed_tera_type = world.assumed_tera_type if world.assumed_tera_type is not None else base.tera_type
        assumed_moves = list(world.assumed_moves) if world.assumed_moves else list(base.moves)

        confirmed_moves = list(base.confirmed_moves)
        assumed_only = [move for move in assumed_moves if move not in confirmed_moves]

        candidates.append(
            CandidateSet(
                species=base.species,
                label=base.label,
                moves=assumed_moves,
                item=assumed_item,
                ability=assumed_ability,
                tera_type=assumed_tera_type,
                spread_label=base.spread_label,
                nature=base.nature,
                evs=dict(base.evs),
                ivs=dict(base.ivs),
                prior_weight=base.prior_weight,
                compatibility_weight=base.compatibility_weight,
                evidence_weight=base.evidence_weight,
                final_weight=world.weight,
                source=base.source,
                confirmed_moves=confirmed_moves,
                assumed_moves=assumed_only,
                notes=list(base.notes),
                penalties=list(base.penalties),
                elimination_reasons=list(base.elimination_reasons),
            )
        )

    candidates = renormalize_candidates(candidates)

    return InferenceResult(
        species=worlds[0].species,
        candidates=candidates,
        confidence_label="branch_distribution",
        notes=["Converted opponent world distribution into inference distribution for branch reweighting."],
    )


def inference_to_worlds(
    inference: InferenceResult,
    template_worlds: list[OpponentWorld],
) -> list[OpponentWorld]:
    if not inference.candidates:
        return []

    template_by_label = {
        world.candidate.label: world
        for world in template_worlds
    }

    normalized = inference.normalized_weights()
    updated_worlds: list[OpponentWorld] = []

    for candidate in inference.candidates:
        if candidate.is_eliminated:
            continue

        template = template_by_label.get(candidate.label)
        if template is None:
            continue

        updated_worlds.append(
            OpponentWorld(
                species=inference.species,
                candidate=candidate,
                weight=normalized.get(candidate.label, 0.0),
                known_moves=list(template.known_moves),
                assumed_moves=list(candidate.moves),
                assumed_item=candidate.item,
                assumed_ability=candidate.ability,
                assumed_tera_type=candidate.tera_type,
                assumed_spread_label=candidate.spread_label,
                notes=list(template.notes) + list(inference.notes[-3:]),
            )
        )

    return updated_worlds