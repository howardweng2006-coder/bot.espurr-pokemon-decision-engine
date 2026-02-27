import json
from pathlib import Path
from typing import List, Tuple, Dict, Any

TYPE_CHART_PATH = Path(__file__).resolve().parents[2] / "data" / "typeChart.json"

_type_chart_cache: Dict[str, Any] | None = None

def load_type_chart() -> Dict[str, Any]:
    global _type_chart_cache
    if _type_chart_cache is None:
        with open(TYPE_CHART_PATH, "r", encoding="utf-8") as f:
            _type_chart_cache = json.load(f)
    return _type_chart_cache

def single_multiplier(move_type: str, defender_type: str) -> float:
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
    # defender_types: ["Water"] or ["Water","Flying"]
    breakdown = []
    mult = 1.0

    for t in defender_types:
        m = single_multiplier(move_type, t)
        breakdown.append({"defenderType": t, "multiplier": m})
        mult *= m

    # Normalize -0.0 type edge cases
    if mult == -0.0:
        mult = 0.0

    return mult, breakdown