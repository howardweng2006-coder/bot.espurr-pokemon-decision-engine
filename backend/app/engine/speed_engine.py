from __future__ import annotations

from typing import Any, List, Tuple

from app.domain.battle_state import PokemonState


def stage_multiplier(stage: int) -> float:
    stage = max(-6, min(6, int(stage)))
    if stage >= 0:
        return (2 + stage) / 2
    return 2 / (2 - stage)


def effective_speed(pokemon: PokemonState) -> float:
    speed = max(1.0, float(pokemon.spe or 100))
    speed *= stage_multiplier(pokemon.boosts.spe)
    return speed


def priority_of(move: Any) -> int:
    return int(getattr(move, "priority", 0) or 0)


def turn_order_context(
    attacking_pokemon: PokemonState,
    defending_pokemon: PokemonState,
    move: Any,
) -> Tuple[str, List[str]]:
    notes: List[str] = []

    move_priority = priority_of(move)
    if move_priority > 0:
        notes.append(f"Positive move priority applied: {move_priority}.")
        return "attacker_first", notes
    if move_priority < 0:
        notes.append(f"Negative move priority applied: {move_priority}.")
        return "attacker_second", notes

    attacker_speed = effective_speed(attacking_pokemon)
    defender_speed = effective_speed(defending_pokemon)

    if attacking_pokemon.boosts.spe != 0:
        notes.append(f"Attacking Pokémon Speed boost stage applied: {attacking_pokemon.boosts.spe}.")
    if defending_pokemon.boosts.spe != 0:
        notes.append(f"Defending Pokémon Speed boost stage applied: {defending_pokemon.boosts.spe}.")

    notes.append(
        f"Estimated speed check: attacker {attacker_speed:.1f} vs defender {defender_speed:.1f}."
    )

    if attacker_speed > defender_speed:
        notes.append("Attacking Pokémon is estimated to move first.")
        return "attacker_first", notes
    if attacker_speed < defender_speed:
        notes.append("Attacking Pokémon is estimated to move second.")
        return "attacker_second", notes

    notes.append("Speeds are tied; turn order treated as uncertain.")
    return "speed_tie", notes


def turn_order_score_adjustment(
    order_context: str,
    min_pct: float,
    max_pct: float,
    category: str,
    base_power: int,
) -> Tuple[float, List[str]]:
    notes: List[str] = []

    if category == "status" or base_power <= 0:
        return 0.0, notes

    adjustment = 0.0

    if order_context == "attacker_first":
        if max_pct >= 100.0:
            adjustment += 20.0
            notes.append("Major boost: priority move can secure KO before opponent acts.")
        elif min_pct >= 50.0:
            adjustment += 2.0
            notes.append("Score slightly boosted because attacker likely moves first with meaningful damage pressure.")

    elif order_context == "attacker_second":
        if max_pct < 100.0:
            adjustment -= 4.0
            notes.append("Score penalized because attacker likely moves second without immediate KO pressure.")
        else:
            adjustment -= 1.0
            notes.append("Score slightly penalized because attacker likely moves second.")

    elif order_context == "speed_tie":
        adjustment -= 0.5
        notes.append("Score slightly reduced because speed tie makes turn order uncertain.")

    return adjustment, notes