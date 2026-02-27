from typing import List, Tuple
from app.services.type_effectiveness import combined_multiplier

def compute_stab(move_type: str, attacker_types: List[str]) -> float:
    return 1.5 if move_type in attacker_types else 1.0

def estimate_damage(attacker, defender, move) -> Tuple[float, float, float, float, List[str]]:
    notes: List[str] = []

    move_type = move.type
    move_power = move.power or 0
    move_category = move.category

    # Status / non-damaging
    if move_category == "status" or move_power <= 0:
        notes.append("Non-damaging move (status or 0 power).")
        return 0.0, 0.0, compute_stab(move_type, attacker.types), 1.0, notes

    stab = compute_stab(move_type, attacker.types)
    type_mult, _ = combined_multiplier(move_type, defender.types)

    if type_mult == 0.0:
        notes.append("No effect (immunity).")
        return 0.0, 0.0, stab, type_mult, notes

    # Pick stats
    if move_category == "physical":
        attack_stat = attacker.atk or 100
        defense_stat = defender.def_ or 100
    else:
        attack_stat = attacker.spa or 100
        defense_stat = defender.spd or 100

    # Simplified damage-like formula
    damage_raw = move_power * (attack_stat / defense_stat)

    damage = damage_raw * stab * type_mult

    SCALE = 0.35  # tune later
    damage *= SCALE

    defender_hp = defender.hp or 100
    damage_percent = (damage / defender_hp) * 100.0
    damage_percent = max(0.0, min(damage_percent, 100.0))

    notes.append("Simplified estimate (not the full Pokémon damage formula).")
    return damage, damage_percent, stab, type_mult, notes