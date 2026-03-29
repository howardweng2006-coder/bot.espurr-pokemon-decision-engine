from __future__ import annotations

from typing import Any, Dict, List, Tuple

from app.providers.type_chart_provider import load_type_chart


def single_multiplier(move_type: str, defender_type: str | None) -> float:
    chart = load_type_chart()

    if move_type not in chart:
        raise ValueError(f"Unknown move type: {move_type}")
    if defender_type is None:
        return 1.0

    entry = chart[move_type]
    if defender_type in entry["zero"]:
        return 0.0
    if defender_type in entry["double"]:
        return 2.0
    if defender_type in entry["half"]:
        return 0.5
    return 1.0


def combined_multiplier(move_type: str, defender_types: List[str]) -> Tuple[float, List[Dict[str, Any]]]:
    breakdown: List[Dict[str, Any]] = []
    mult = 1.0

    for defender_type in defender_types:
        multiplier = single_multiplier(move_type, defender_type)
        breakdown.append(
            {
                "defenderType": defender_type,
                "multiplier": multiplier,
            }
        )
        mult *= multiplier

    if mult == -0.0:
        mult = 0.0

    return mult, breakdown