from __future__ import annotations

from typing import Dict, List, Tuple
import math

from app.services.damage_preview import estimate_damage
from app.schemas.damage_preview import CombatantInfo, MoveInfo


def _softmax(values: Dict[str, float], temperature: float = 8.0) -> Dict[str, float]:
    """
    Returns probability-like confidences that sum to 1.
    Higher temperature => flatter distribution.
    """
    if not values:
        return {}

    # numerical stability
    max_v = max(values.values())
    exps = {k: math.exp((v - max_v) / max(temperature, 1e-6)) for k, v in values.items()}
    total = sum(exps.values()) or 1.0
    return {k: exps[k] / total for k in values}


def _score_move(
    damage_pct: float,
    type_mult: float,
    category: str,
    base_power: int,
) -> float:
    """
    MVP scoring heuristic:
    - Primary objective: deal more % damage
    - Prefer super-effective lines slightly
    - Penalize non-damaging/status in this MVP
    """
    if category == "status" or base_power <= 0:
        return -5.0  # status moves are "bad" in this MVP

    # Base score is damage percent
    score = damage_pct

    # Small bonus for strong effectiveness; small penalty for resisted
    # (damage_pct already includes this, but this helps separate close ties)
    if type_mult >= 2.0:
        score += 5.0
    elif 0.0 < type_mult < 1.0:
        score -= 3.0
    elif type_mult == 0.0:
        score -= 100.0

    return score


def suggest_move(
    attacker: CombatantInfo,
    defender: CombatantInfo,
    moves: List[MoveInfo],
    temperature: float = 8.0,
) -> Tuple[str, float, List[dict], str]:
    """
    Returns:
      best_move_name, best_confidence, ranked_moves(list of dicts), explanation
    """
    results: List[dict] = []
    raw_scores: Dict[str, float] = {}

    for idx, move in enumerate(moves):
        # Ensure every move has a usable label
        move_name = (move.name or f"Move {idx+1}").strip()

        damage, damage_pct, stab, type_mult, notes = estimate_damage(
            attacker=attacker,
            defender=defender,
            move=move,
        )

        base_power = move.power or 0
        score = _score_move(
            damage_pct=damage_pct,
            type_mult=type_mult,
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
                "stab": stab,
                "typeMultiplier": type_mult,
                "estimatedDamage": damage,
                "estimatedDamagePercent": damage_pct,
                "score": score,
                "confidence": 0.0,  # filled after softmax
                "notes": notes,
            }
        )

    confidences = _softmax(raw_scores, temperature=temperature)

    # Attach confidences + sort
    for r in results:
        r["confidence"] = confidences.get(r["name"], 0.0)

    results.sort(key=lambda x: x["score"], reverse=True)

    best_move = results[0]["name"]
    best_conf = results[0]["confidence"]

    # Simple explanation (MVP)
    top = results[0]
    explanation = (
        f"Recommended {best_move} because it scores highest in this MVP heuristic "
        f"(~{top['estimatedDamagePercent']:.1f}% estimated damage, "
        f"{top['typeMultiplier']}x effectiveness, STAB {top['stab']})."
    )

    return best_move, best_conf, results, explanation