from __future__ import annotations

from typing import Any, List, Tuple

from app.engine.type_engine import combined_multiplier


def compute_stab(move_type: str, attacker_types: List[str], tera_active: bool = False) -> float:
    if move_type not in attacker_types:
        return 1.0
    return 2.0 if tera_active else 1.5


def pick_damage_stats(attacker: Any, defender: Any, move_category: str) -> Tuple[float, float]:
    if move_category == "physical":
        attack_stat = attacker.atk or 100
        defense_stat = defender.def_ or 100
    else:
        attack_stat = attacker.spa or 100
        defense_stat = defender.spd or 100

    attack_stat = max(1.0, float(attack_stat))
    defense_stat = max(1.0, float(defense_stat))
    return attack_stat, defense_stat


def estimate_damage(attacker: Any, defender: Any, move: Any) -> dict:
    notes: List[str] = []

    move_type = move.type
    move_power = move.power or 0
    move_category = move.category

    level = getattr(move, "level", None) or getattr(attacker, "level", None) or 50
    crit = bool(getattr(move, "crit", False))
    attacker_burned = bool(getattr(attacker, "burned", False))
    tera_active = bool(getattr(attacker, "tera_active", False))

    if move_category == "status" or move_power <= 0:
        notes.append("Non-damaging move (status or 0 power).")
        stab = compute_stab(move_type, attacker.types, tera_active=tera_active)
        return {
            "minDamage": 0.0,
            "maxDamage": 0.0,
            "minPercent": 0.0,
            "maxPercent": 0.0,
            "stab": stab,
            "typeMultiplier": 1.0,
            "level": level,
            "critApplied": False,
            "burnApplied": False,
            "notes": notes,
        }

    stab = compute_stab(move_type, attacker.types, tera_active=tera_active)
    type_mult, _ = combined_multiplier(move_type, defender.types)

    if type_mult == 0.0:
        notes.append("No effect (immunity).")
        return {
            "minDamage": 0.0,
            "maxDamage": 0.0,
            "minPercent": 0.0,
            "maxPercent": 0.0,
            "stab": stab,
            "typeMultiplier": type_mult,
            "level": level,
            "critApplied": crit,
            "burnApplied": False,
            "notes": notes,
        }

    attack_stat, defense_stat = pick_damage_stats(attacker, defender, move_category)

    base_damage = ((((2 * level) / 5 + 2) * move_power * (attack_stat / defense_stat)) / 50) + 2

    crit_mod = 1.5 if crit else 1.0
    burn_mod = 0.5 if (attacker_burned and move_category == "physical") else 1.0

    if crit:
        notes.append("Critical hit modifier applied.")
    if burn_mod < 1.0:
        notes.append("Burn penalty applied to physical damage.")

    min_random = 0.85
    max_random = 1.00

    min_damage = base_damage * stab * type_mult * crit_mod * burn_mod * min_random
    max_damage = base_damage * stab * type_mult * crit_mod * burn_mod * max_random

    defender_hp = max(1.0, float(defender.hp or 100))
    min_percent = max(0.0, min((min_damage / defender_hp) * 100.0, 100.0))
    max_percent = max(0.0, min((max_damage / defender_hp) * 100.0, 100.0))

    notes.append("Gen-style level-based estimate with random damage range (0.85–1.00).")

    return {
        "minDamage": min_damage,
        "maxDamage": max_damage,
        "minPercent": min_percent,
        "maxPercent": max_percent,
        "stab": stab,
        "typeMultiplier": type_mult,
        "level": level,
        "critApplied": crit,
        "burnApplied": burn_mod < 1.0,
        "notes": notes,
    }