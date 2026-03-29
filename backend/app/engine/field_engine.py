from __future__ import annotations

from typing import Any, List, Tuple

from app.domain.battle_state import FieldState, PokemonState, SideConditions
from app.engine.type_engine import combined_multiplier


def weather_modifier(field: FieldState, move: Any) -> Tuple[float, List[str]]:
    if not field.weather:
        return 1.0, []

    notes: List[str] = []
    move_type = move.type
    weather = field.weather

    if weather == "sun":
        if move_type == "Fire":
            notes.append("Sun boosted Fire-type move power.")
            return 1.5, notes
        if move_type == "Water":
            notes.append("Sun weakened Water-type move power.")
            return 0.5, notes

    if weather == "rain":
        if move_type == "Water":
            notes.append("Rain boosted Water-type move power.")
            return 1.5, notes
        if move_type == "Fire":
            notes.append("Rain weakened Fire-type move power.")
            return 0.5, notes

    return 1.0, notes


def terrain_modifier(field: FieldState, move: Any) -> Tuple[float, List[str]]:
    if not field.terrain:
        return 1.0, []

    notes: List[str] = []
    move_type = move.type
    terrain = field.terrain

    if terrain == "electric" and move_type == "Electric":
        notes.append("Electric Terrain boosted Electric-type move power (groundedness not yet modeled).")
        return 1.3, notes

    if terrain == "grassy" and move_type == "Grass":
        notes.append("Grassy Terrain boosted Grass-type move power (groundedness not yet modeled).")
        return 1.3, notes

    if terrain == "psychic" and move_type == "Psychic":
        notes.append("Psychic Terrain boosted Psychic-type move power (groundedness not yet modeled).")
        return 1.3, notes

    return 1.0, notes


def apply_field_modifiers(
    dmg: dict,
    move: Any,
    field: FieldState,
    defender_hp: float,
) -> Tuple[dict, List[str]]:
    weather_mod, weather_notes = weather_modifier(field, move)
    terrain_mod, terrain_notes = terrain_modifier(field, move)

    combined_mod = weather_mod * terrain_mod

    if combined_mod == 1.0:
        return dmg, weather_notes + terrain_notes

    min_damage = dmg["minDamage"] * combined_mod
    max_damage = dmg["maxDamage"] * combined_mod

    min_percent = max(0.0, min((min_damage / defender_hp) * 100.0, 100.0))
    max_percent = max(0.0, min((max_damage / defender_hp) * 100.0, 100.0))

    adjusted = dict(dmg)
    adjusted["minDamage"] = min_damage
    adjusted["maxDamage"] = max_damage
    adjusted["minPercent"] = min_percent
    adjusted["maxPercent"] = max_percent

    return adjusted, weather_notes + terrain_notes


def is_grounded(pokemon: PokemonState) -> bool:
    return "Flying" not in pokemon.types


def stealth_rock_percent(pokemon: PokemonState) -> float:
    rock_mult, _ = combined_multiplier("Rock", pokemon.types)
    return 12.5 * rock_mult


def spikes_percent(pokemon: PokemonState, layers: int) -> float:
    if layers <= 0 or not is_grounded(pokemon):
        return 0.0
    if layers == 1:
        return 12.5
    if layers == 2:
        return 100.0 / 6.0
    return 25.0


def hazard_on_entry_context(
    switch_target: PokemonState,
    side_conditions: SideConditions,
) -> Tuple[dict, List[str]]:
    notes: List[str] = []

    sr_pct = 0.0
    spikes_pct = 0.0
    sticky_web_penalty = 0.0
    tspikes_penalty = 0.0

    if side_conditions.stealth_rock:
        sr_pct = stealth_rock_percent(switch_target)
        notes.append(f"Stealth Rock would deal about {sr_pct:.1f}% on entry.")

    if side_conditions.spikes_layers > 0:
        spikes_pct = spikes_percent(switch_target, side_conditions.spikes_layers)
        if spikes_pct > 0:
            notes.append(
                f"Spikes ({side_conditions.spikes_layers} layer{'s' if side_conditions.spikes_layers != 1 else ''}) "
                f"would deal about {spikes_pct:.1f}% on entry."
            )
        else:
            notes.append("Spikes present, but switch target is treated as not grounded.")

    if side_conditions.sticky_web:
        if is_grounded(switch_target):
            sticky_web_penalty = 4.0
            notes.append("Sticky Web would lower Speed on entry (first-pass heuristic penalty applied).")
        else:
            notes.append("Sticky Web present, but switch target is treated as not grounded.")

    if side_conditions.toxic_spikes_layers > 0:
        if (
            is_grounded(switch_target)
            and "Steel" not in switch_target.types
            and "Poison" not in switch_target.types
        ):
            tspikes_penalty = 6.0 if side_conditions.toxic_spikes_layers >= 2 else 4.0
            notes.append("Toxic Spikes would inflict status on entry (first-pass heuristic penalty applied).")
        elif "Poison" in switch_target.types:
            notes.append("Poison-type switch target would absorb Toxic Spikes (first-pass note only).")
        else:
            notes.append("Toxic Spikes present, but switch target avoids them in this simplified model.")

    total_entry_pct = sr_pct + spikes_pct

    return {
        "stealthRockPercent": sr_pct,
        "spikesPercent": spikes_pct,
        "totalEntryPercent": total_entry_pct,
        "stickyWebPenalty": sticky_web_penalty,
        "toxicSpikesPenalty": tspikes_penalty,
    }, notes