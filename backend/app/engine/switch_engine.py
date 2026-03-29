from __future__ import annotations

from typing import List, Tuple

from app.domain.battle_state import PokemonState, SideConditions
from app.engine.field_engine import hazard_on_entry_context
from app.engine.speed_engine import effective_speed
from app.engine.type_engine import combined_multiplier


def score_switch(
    switch_target: PokemonState,
    opposing_active: PokemonState,
    entry_side_conditions: SideConditions,
) -> Tuple[float, List[str]]:
    notes: List[str] = []

    defense_multiplier = 1.0
    for opposing_type in opposing_active.types:
        mult, _ = combined_multiplier(opposing_type, switch_target.types)
        defense_multiplier *= mult

    score = 50.0

    if defense_multiplier == 0.0:
        score += 30.0
        notes.append("Switch target appears immune to opposing active Pokémon's STAB profile.")
    elif defense_multiplier <= 0.25:
        score += 20.0
        notes.append("Switch target strongly resists opposing active Pokémon's STAB profile.")
    elif defense_multiplier <= 0.5:
        score += 12.0
        notes.append("Switch target resists opposing active Pokémon's STAB profile.")
    elif defense_multiplier >= 4.0:
        score -= 30.0
        notes.append("Switch target appears extremely vulnerable to opposing active Pokémon's STAB profile.")
    elif defense_multiplier >= 2.0:
        score -= 18.0
        notes.append("Switch target appears weak to opposing active Pokémon's STAB profile.")

    current_hp = float(switch_target.current_hp if switch_target.current_hp is not None else switch_target.hp or 100)
    max_hp = max(1.0, float(switch_target.hp or 100))
    hp_ratio = current_hp / max_hp

    score += (hp_ratio - 0.5) * 20.0
    notes.append(f"Switch target HP ratio considered: {hp_ratio:.2f}.")

    hazard_context, hazard_notes = hazard_on_entry_context(
        switch_target=switch_target,
        side_conditions=entry_side_conditions,
    )
    notes.extend(hazard_notes)

    total_entry_pct = float(hazard_context["totalEntryPercent"])
    if total_entry_pct > 0:
        score -= total_entry_pct * 0.8
        notes.append(f"Switch score penalized for entry hazard chip: {total_entry_pct:.1f}%.")

    score -= float(hazard_context["stickyWebPenalty"])
    score -= float(hazard_context["toxicSpikesPenalty"])

    post_entry_hp_ratio = max(0.0, hp_ratio - total_entry_pct / 100.0)
    notes.append(f"Estimated post-entry HP ratio: {post_entry_hp_ratio:.2f}.")

    switch_speed = effective_speed(switch_target)
    opposing_speed = effective_speed(opposing_active)
    if switch_speed > opposing_speed:
        score += 3.0
        notes.append("Switch target is estimated to outspeed opposing active Pokémon.")
    elif switch_speed < opposing_speed:
        score -= 2.0
        notes.append("Switch target is estimated to be slower than opposing active Pokémon.")

    return score, notes