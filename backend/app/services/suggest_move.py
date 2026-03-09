from __future__ import annotations

from typing import Dict, List, Tuple
import math

from app.services.damage_preview import estimate_damage
from app.schemas.damage_preview import CombatantInfo, MoveInfo


def _softmax(values: Dict[str, float], temperature: float = 8.0) -> Dict[str, float]:
    if not values:
        return {}

    max_v = max(values.values())
    exps = {k: math.exp((v - max_v) / max(temperature, 1e-6)) for k, v in values.items()}
    total = sum(exps.values()) or 1.0
    return {k: exps[k] / total for k in values}


def _score_move(
    min_pct: float,
    max_pct: float,
    type_mult: float,
    category: str,
    base_power: int,
) -> float:
    if category == "status" or base_power <= 0:
        return -5.0

    avg_pct = (min_pct + max_pct) / 2.0
    score = avg_pct

    if type_mult >= 2.0:
        score += 5.0
    elif 0.0 < type_mult < 1.0:
        score -= 3.0
    elif type_mult == 0.0:
        score -= 100.0

    # mild KO pressure bonus
    if min_pct >= 100.0:
        score += 15.0
    elif max_pct >= 100.0:
        score += 8.0

    return score


def suggest_move(
    attacker: CombatantInfo,
    defender: CombatantInfo,
    moves: List[MoveInfo],
    temperature: float = 8.0,
) -> Tuple[str, float, List[dict], str]:
    results: List[dict] = []
    raw_scores: Dict[str, float] = {}

    for idx, move in enumerate(moves):
        move_name = (move.name or f"Move {idx+1}").strip()

        dmg = estimate_damage(
            attacker=attacker,
            defender=defender,
            move=move,
        )

        base_power = move.power or 0
        score = _score_move(
            min_pct=dmg["minPercent"],
            max_pct=dmg["maxPercent"],
            type_mult=dmg["typeMultiplier"],
            category=move.category,
            base_power=base_power,
        )

        raw_scores[move_name] = score
        results.append(
            {
                "name": move_name,
                "moveType": move.type,
                "moveCategory": move.category,
                "basePower": base_power,
                "stab": dmg["stab"],
                "typeMultiplier": dmg["typeMultiplier"],
                "minDamage": dmg["minDamage"],
                "maxDamage": dmg["maxDamage"],
                "minDamagePercent": dmg["minPercent"],
                "maxDamagePercent": dmg["maxPercent"],
                "score": score,
                "confidence": 0.0,
                "notes": dmg["notes"],
            }
        )

    confidences = _softmax(raw_scores, temperature=temperature)

    for r in results:
        r["confidence"] = confidences.get(r["name"], 0.0)

    results.sort(key=lambda x: x["score"], reverse=True)

    best_move = results[0]["name"]
    best_conf = results[0]["confidence"]
    top = results[0]

    explanation = (
        f"Recommended {best_move} because it scores highest in this MVP heuristic "
        f"({top['minDamagePercent']:.1f}–{top['maxDamagePercent']:.1f}% estimated damage, "
        f"{top['typeMultiplier']}x effectiveness, STAB {top['stab']})."
    )

    return best_move, best_conf, results, explanation