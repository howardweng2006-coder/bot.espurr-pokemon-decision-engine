from __future__ import annotations

from typing import List

from app.domain.actions import EvaluatedAction
from app.domain.battle_state import BattleState
from app.inference.models import InferenceResult


def build_assumptions(
    state: BattleState,
    inference: InferenceResult | None = None,
) -> List[str]:
    assumptions: List[str] = [
        f"Format context placeholder: Gen {state.format_context.generation} / {state.format_context.format_name}.",
        "Current evaluator is shallow and mostly single-turn.",
        "Only relevant offensive/defensive stat boosts are currently applied.",
    ]

    if state.field.weather:
        assumptions.append(
            "Weather currently models only standard Fire/Water power changes for sun and rain."
        )

    if state.field.terrain:
        assumptions.append(
            "Terrain currently models offensive type boosts only; groundedness and other terrain effects are not yet modeled."
        )

    assumptions.append(
        "Turn order currently uses move priority, Speed stat, and Speed boosts."
    )
    assumptions.append(
        "Move survivability uses a proxy retaliation estimate based on a plausible strong opposing active STAB attack."
    )
    assumptions.append(
        "Proxy retaliation does not yet model exact movesets, items, abilities, priority on retaliation, or confidence-weighted set inference."
    )
    assumptions.append(
        "Switch scoring is a first-pass heuristic based on opposing active STAB profile, HP ratio, rough speed context, and entry hazards."
    )
    assumptions.append(
        "Hazard handling currently models Stealth Rock, Spikes, Sticky Web, and Toxic Spikes with simplified groundedness/status logic."
    )
    assumptions.append(
        "Opponent coverage moves, removal options, and long-term positioning are not yet modeled in switch evaluation."
    )

    if inference is not None:
        assumptions.append(
            f"Inference confidence is currently '{inference.confidence_label}' for the opposing active Pokémon."
        )
        assumptions.extend(inference.notes)

    return assumptions


def build_recommendation_explanation(top_action: EvaluatedAction) -> str:
    if top_action.action_type == "move":
        min_pct = top_action.min_damage_percent if top_action.min_damage_percent is not None else 0.0
        max_pct = top_action.max_damage_percent if top_action.max_damage_percent is not None else 0.0
        type_mult = top_action.type_multiplier if top_action.type_multiplier is not None else 1.0

        return (
            f"Recommended action: use {top_action.name}. "
            f"It currently scores highest "
            f"({min_pct:.1f}–{max_pct:.1f}% estimated damage, "
            f"{type_mult}x effectiveness)."
        )

    return (
        f"Recommended action: switch to {top_action.name}. "
        f"It currently scores highest based on defensive matchup and board-position heuristics."
    )


def summarize_top_action_notes(
    top_action: EvaluatedAction,
    limit: int = 3,
) -> List[str]:
    notes = [note.strip() for note in top_action.notes if note and note.strip()]
    return notes[:limit]


def build_reasoning_summary(
    top_action: EvaluatedAction,
    limit: int = 3,
) -> str:
    top_notes = summarize_top_action_notes(top_action, limit=limit)
    if not top_notes:
        return "No additional reasoning notes are currently available."

    joined = " ".join(top_notes)
    return f"Key reasons: {joined}"


def build_inference_summary(inference: InferenceResult | None) -> str:
    if inference is None:
        return "No opponent-set inference summary is currently available."

    if not inference.candidates:
        return "No plausible opposing active set candidates are currently available."

    normalized = inference.normalized_weights()
    top_candidate = max(inference.candidates, key=lambda candidate: candidate.weight)
    top_weight = normalized.get(top_candidate.label, 0.0)

    return (
        f"Opponent active inference: top candidate is '{top_candidate.label}' "
        f"with placeholder confidence {top_weight:.2f}."
    )