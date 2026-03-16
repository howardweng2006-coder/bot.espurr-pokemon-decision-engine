from __future__ import annotations

import math
from dataclasses import replace
from types import SimpleNamespace
from typing import Dict, List, Tuple

from app.domain.battle_state import ActivePokemon, BattleState, FieldState, SideHazards, StatBoosts
from app.schemas.damage_preview import CombatantInfo, MoveInfo
from app.services.damage_preview import estimate_damage
from app.services.type_effectiveness import combined_multiplier


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

    if min_pct >= 100.0:
        score += 15.0
    elif max_pct >= 100.0:
        score += 8.0

    return score


def _stage_multiplier(stage: int) -> float:
    stage = max(-6, min(6, int(stage)))
    if stage >= 0:
        return (2 + stage) / 2
    return 2 / (2 - stage)


def _apply_relevant_boosts(
    attacker: ActivePokemon,
    defender: ActivePokemon,
    move_category: str,
) -> Tuple[ActivePokemon, ActivePokemon, List[str]]:
    notes: List[str] = []

    if move_category == "physical":
        atk_mult = _stage_multiplier(attacker.boosts.atk)
        def_mult = _stage_multiplier(defender.boosts.def_)

        boosted_attacker = replace(attacker, atk=attacker.atk * atk_mult)
        boosted_defender = replace(defender, def_=defender.def_ * def_mult)

        if attacker.boosts.atk != 0:
            notes.append(f"Attacker Attack boost stage applied: {attacker.boosts.atk}.")
        if defender.boosts.def_ != 0:
            notes.append(f"Defender Defense boost stage applied: {defender.boosts.def_}.")

        return boosted_attacker, boosted_defender, notes

    if move_category == "special":
        spa_mult = _stage_multiplier(attacker.boosts.spa)
        spd_mult = _stage_multiplier(defender.boosts.spd)

        boosted_attacker = replace(attacker, spa=attacker.spa * spa_mult)
        boosted_defender = replace(defender, spd=defender.spd * spd_mult)

        if attacker.boosts.spa != 0:
            notes.append(f"Attacker Special Attack boost stage applied: {attacker.boosts.spa}.")
        if defender.boosts.spd != 0:
            notes.append(f"Defender Special Defense boost stage applied: {defender.boosts.spd}.")

        return boosted_attacker, boosted_defender, notes

    return attacker, defender, notes


def _weather_modifier(field, move) -> Tuple[float, List[str]]:
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


def _terrain_modifier(field, move) -> Tuple[float, List[str]]:
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


def _apply_field_modifiers(
    dmg: dict,
    move,
    field,
    defender_hp: float,
) -> Tuple[dict, List[str]]:
    weather_mod, weather_notes = _weather_modifier(field, move)
    terrain_mod, terrain_notes = _terrain_modifier(field, move)

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


def _effective_speed(pokemon: ActivePokemon) -> float:
    speed = max(1.0, float(pokemon.spe or 100))
    speed *= _stage_multiplier(pokemon.boosts.spe)
    return speed


def _priority_of(move) -> int:
    return int(getattr(move, "priority", 0) or 0)


def _turn_order_context(
    attacker: ActivePokemon,
    defender: ActivePokemon,
    move,
) -> Tuple[str, List[str]]:
    notes: List[str] = []

    move_priority = _priority_of(move)
    if move_priority > 0:
        notes.append(f"Positive move priority applied: {move_priority}.")
        return "attacker_first", notes
    if move_priority < 0:
        notes.append(f"Negative move priority applied: {move_priority}.")
        return "attacker_second", notes

    attacker_speed = _effective_speed(attacker)
    defender_speed = _effective_speed(defender)

    if attacker.boosts.spe != 0:
        notes.append(f"Attacker Speed boost stage applied: {attacker.boosts.spe}.")
    if defender.boosts.spe != 0:
        notes.append(f"Defender Speed boost stage applied: {defender.boosts.spe}.")

    notes.append(
        f"Estimated speed check: attacker {attacker_speed:.1f} vs defender {defender_speed:.1f}."
    )

    if attacker_speed > defender_speed:
        notes.append("Attacker is estimated to move first.")
        return "attacker_first", notes
    if attacker_speed < defender_speed:
        notes.append("Attacker is estimated to move second.")
        return "attacker_second", notes

    notes.append("Speeds are tied; turn order treated as uncertain.")
    return "speed_tie", notes


def _turn_order_score_adjustment(
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
            adjustment += 6.0
            notes.append("Score boosted because attacker likely moves first and can threaten an immediate KO.")
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


def _best_stab_type_into_target(attacker: ActivePokemon, defender: ActivePokemon) -> Tuple[str | None, float]:
    best_type = None
    best_mult = -1.0

    for stab_type in attacker.types:
        mult, _ = combined_multiplier(stab_type, defender.types)
        if mult > best_mult:
            best_mult = mult
            best_type = stab_type

    if best_type is None:
        return None, 1.0

    return best_type, best_mult


def _proxy_retaliation_move(defender: ActivePokemon, attacker: ActivePokemon):
    best_stab_type, best_mult = _best_stab_type_into_target(defender, attacker)

    if best_stab_type is None:
        best_stab_type = defender.types[0] if defender.types else "Normal"
        best_mult = 1.0

    defender_prefers_physical = float(defender.atk or 100) >= float(defender.spa or 100)
    category = "physical" if defender_prefers_physical else "special"

    # Simple placeholder power choice:
    # stronger if best STAB is favorable into target, otherwise standard decent STAB power.
    power = 100 if best_mult >= 2.0 else 80

    return SimpleNamespace(
        name=f"Proxy {best_stab_type} STAB",
        type=best_stab_type,
        category=category,
        power=power,
        priority=0,
        crit=False,
        level=defender.level,
    )


def _retaliation_context(
    attacker: ActivePokemon,
    defender: ActivePokemon,
) -> Tuple[dict, List[str]]:
    notes: List[str] = []

    proxy_move = _proxy_retaliation_move(defender, attacker)
    notes.append(
        f"Proxy retaliation assumes defender can use a plausible {proxy_move.type}-type STAB attack "
        f"({proxy_move.category}, {proxy_move.power} BP)."
    )

    retaliation = estimate_damage(
        attacker=defender,
        defender=attacker,
        move=proxy_move,
    )

    attacker_current_hp = float(attacker.current_hp if attacker.current_hp is not None else attacker.hp or 100)
    attacker_max_hp = max(1.0, float(attacker.hp or 100))

    retaliation_min_pct_current = max(
        0.0, min((float(retaliation["minDamage"]) / max(1.0, attacker_current_hp)) * 100.0, 100.0)
    )
    retaliation_max_pct_current = max(
        0.0, min((float(retaliation["maxDamage"]) / max(1.0, attacker_current_hp)) * 100.0, 100.0)
    )

    context = {
        "moveType": proxy_move.type,
        "moveCategory": proxy_move.category,
        "power": proxy_move.power,
        "typeMultiplier": retaliation["typeMultiplier"],
        "minDamage": retaliation["minDamage"],
        "maxDamage": retaliation["maxDamage"],
        "minPercentMaxHp": retaliation["minPercent"],
        "maxPercentMaxHp": retaliation["maxPercent"],
        "minPercentCurrentHp": retaliation_min_pct_current,
        "maxPercentCurrentHp": retaliation_max_pct_current,
        "attackerCurrentHp": attacker_current_hp,
        "attackerMaxHp": attacker_max_hp,
    }

    return context, notes


def _survivability_score_adjustment(
    order_context: str,
    retaliation: dict,
    category: str,
    base_power: int,
) -> Tuple[float, List[str]]:
    notes: List[str] = []

    if category == "status" or base_power <= 0:
        return 0.0, notes

    adjustment = 0.0
    max_pct_current = float(retaliation["maxPercentCurrentHp"])
    min_pct_current = float(retaliation["minPercentCurrentHp"])

    if order_context == "attacker_second":
        if min_pct_current >= 100.0:
            adjustment -= 45.0
            notes.append("Heavy penalty: attacker is likely KOed by proxy retaliation before moving.")
        elif max_pct_current >= 100.0:
            adjustment -= 30.0
            notes.append("Strong penalty: attacker may be KOed by proxy retaliation before moving.")
        elif max_pct_current >= 75.0:
            adjustment -= 16.0
            notes.append("Penalty: attacker risks taking very heavy proxy retaliation before moving.")
        elif max_pct_current >= 50.0:
            adjustment -= 8.0
            notes.append("Penalty: attacker risks substantial proxy retaliation before moving.")

    elif order_context == "speed_tie":
        if max_pct_current >= 100.0:
            adjustment -= 12.0
            notes.append("Penalty: speed tie plus proxy retaliation means attacker may be KOed before acting.")
        elif max_pct_current >= 75.0:
            adjustment -= 6.0
            notes.append("Penalty: speed tie makes heavy proxy retaliation risky.")

    return adjustment, notes

def _is_grounded(pokemon: ActivePokemon) -> bool:
    # First-pass simplification:
    # Flying-types are not grounded.
    # Levitate, Air Balloon, Magnet Rise, etc. are not modeled yet.
    return "Flying" not in pokemon.types


def _stealth_rock_percent(pokemon: ActivePokemon) -> float:
    rock_mult, _ = combined_multiplier("Rock", pokemon.types)
    return 12.5 * rock_mult


def _spikes_percent(pokemon: ActivePokemon, layers: int) -> float:
    if layers <= 0 or not _is_grounded(pokemon):
        return 0.0
    if layers == 1:
        return 12.5
    if layers == 2:
        return 100.0 / 6.0  # 16.67%
    return 25.0


def _hazard_on_entry_context(
    switch_target: ActivePokemon,
    side_hazards: SideHazards,
) -> Tuple[dict, List[str]]:
    notes: List[str] = []

    print("side_hazards in _hazard_on_entry_context:", side_hazards)

    sr_pct = 0.0
    spikes_pct = 0.0
    sticky_web_penalty = 0.0
    tspikes_penalty = 0.0

    if side_hazards.stealth_rock:
        sr_pct = _stealth_rock_percent(switch_target)
        notes.append(f"Stealth Rock would deal about {sr_pct:.1f}% on entry.")

    if side_hazards.spikes_layers > 0:
        spikes_pct = _spikes_percent(switch_target, side_hazards.spikes_layers)
        if spikes_pct > 0:
            notes.append(
                f"Spikes ({side_hazards.spikes_layers} layer{'s' if side_hazards.spikes_layers != 1 else ''}) "
                f"would deal about {spikes_pct:.1f}% on entry."
            )
        else:
            notes.append("Spikes present, but switch target is treated as not grounded.")

    if side_hazards.sticky_web:
        if _is_grounded(switch_target):
            sticky_web_penalty = 4.0
            notes.append("Sticky Web would lower Speed on entry (first-pass heuristic penalty applied).")
        else:
            notes.append("Sticky Web present, but switch target is treated as not grounded.")

    if side_hazards.toxic_spikes_layers > 0:
        if _is_grounded(switch_target) and "Steel" not in switch_target.types and "Poison" not in switch_target.types:
            tspikes_penalty = 6.0 if side_hazards.toxic_spikes_layers >= 2 else 4.0
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

def _score_switch(
    switch_target: ActivePokemon,
    defender: ActivePokemon,
    attacker_side_hazards: SideHazards,
) -> Tuple[float, List[str]]:
    notes: List[str] = []

    defense_multiplier = 1.0
    for defender_type in defender.types:
        mult, _ = combined_multiplier(defender_type, switch_target.types)
        defense_multiplier *= mult

    score = 50.0

    if defense_multiplier == 0.0:
        score += 30.0
        notes.append("Switch target appears immune to defender's STAB profile.")
    elif defense_multiplier <= 0.25:
        score += 20.0
        notes.append("Switch target strongly resists defender's STAB profile.")
    elif defense_multiplier <= 0.5:
        score += 12.0
        notes.append("Switch target resists defender's STAB profile.")
    elif defense_multiplier >= 4.0:
        score -= 30.0
        notes.append("Switch target appears extremely vulnerable to defender's STAB profile.")
    elif defense_multiplier >= 2.0:
        score -= 18.0
        notes.append("Switch target appears weak to defender's STAB profile.")

    current_hp = float(switch_target.current_hp if switch_target.current_hp is not None else switch_target.hp or 100)
    max_hp = max(1.0, float(switch_target.hp or 100))
    hp_ratio = current_hp / max_hp

    score += (hp_ratio - 0.5) * 20.0
    notes.append(f"Switch target HP ratio considered: {hp_ratio:.2f}.")

    hazard_context, hazard_notes = _hazard_on_entry_context(
        switch_target=switch_target,
        side_hazards=attacker_side_hazards,
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

    speed = _effective_speed(switch_target)
    defender_speed = _effective_speed(defender)
    if speed > defender_speed:
        score += 3.0
        notes.append("Switch target is estimated to outspeed defender.")
    elif speed < defender_speed:
        score -= 2.0
        notes.append("Switch target is estimated to be slower than defender.")

    return score, notes


def _field_assumptions(field) -> List[str]:
    assumptions: List[str] = []

    if field.weather:
        assumptions.append(
            "Weather currently models only standard Fire/Water power changes for sun and rain."
        )

    if field.terrain:
        assumptions.append(
            "Terrain currently models offensive type boosts only; groundedness and other terrain effects are not yet modeled."
        )

    assumptions.append(
        "Turn order currently uses move priority, Speed stat, and Speed boosts."
    )
    assumptions.append(
        "Move survivability uses a proxy retaliation estimate based on a plausible strong defender STAB attack."
    )
    assumptions.append(
        "Proxy retaliation does not yet model exact movesets, items, abilities, priority on retaliation, or confidence-weighted set inference."
    )
    assumptions.append(
        "Switch scoring is a first-pass heuristic based on defender STAB profile, HP ratio, rough speed context, and entry hazards."
    )
    assumptions.append(
        "Hazard handling currently models Stealth Rock, Spikes, Sticky Web, and Toxic Spikes with simplified groundedness/status logic."
    )
    assumptions.append(
        "Opponent coverage moves, removal options, and long-term positioning are not yet modeled in switch evaluation."
    )

    return assumptions


def _evaluate_move_actions(state: BattleState) -> List[dict]:
    results: List[dict] = []

    for idx, move in enumerate(state.moves):
        move_name = (move.name or f"Move {idx+1}").strip()

        boosted_attacker, boosted_defender, boost_notes = _apply_relevant_boosts(
            state.attacker,
            state.defender,
            move.category,
        )

        dmg = estimate_damage(
            attacker=boosted_attacker,
            defender=boosted_defender,
            move=move,
        )

        defender_hp = max(1.0, float(boosted_defender.hp or 100))
        dmg, field_notes = _apply_field_modifiers(
            dmg=dmg,
            move=move,
            field=state.field,
            defender_hp=defender_hp,
        )

        order_context, turn_order_notes = _turn_order_context(
            state.attacker,
            state.defender,
            move,
        )

        retaliation, retaliation_notes = _retaliation_context(
            attacker=state.attacker,
            defender=state.defender,
        )

        base_power = move.power or 0
        score = _score_move(
            min_pct=dmg["minPercent"],
            max_pct=dmg["maxPercent"],
            type_mult=dmg["typeMultiplier"],
            category=move.category,
            base_power=base_power,
        )

        turn_adjustment, turn_notes = _turn_order_score_adjustment(
            order_context=order_context,
            min_pct=dmg["minPercent"],
            max_pct=dmg["maxPercent"],
            category=move.category,
            base_power=base_power,
        )
        score += turn_adjustment

        survivability_adjustment, survivability_notes = _survivability_score_adjustment(
            order_context=order_context,
            retaliation=retaliation,
            category=move.category,
            base_power=base_power,
        )
        score += survivability_adjustment

        extra_notes = list(retaliation_notes)
        extra_notes.append(
            f"Proxy retaliation estimate vs attacker current HP: "
            f"{retaliation['minPercentCurrentHp']:.1f}–{retaliation['maxPercentCurrentHp']:.1f}%."
        )

        results.append(
            {
                "actionType": "move",
                "name": move_name,
                "moveType": move.type,
                "moveCategory": move.category,
                "basePower": base_power,
                "typeMultiplier": dmg["typeMultiplier"],
                "minDamage": dmg["minDamage"],
                "maxDamage": dmg["maxDamage"],
                "minDamagePercent": dmg["minPercent"],
                "maxDamagePercent": dmg["maxPercent"],
                "score": score,
                "confidence": 0.0,
                "notes": (
                    dmg["notes"]
                    + boost_notes
                    + field_notes
                    + turn_order_notes
                    + extra_notes
                    + turn_notes
                    + survivability_notes
                ),
            }
        )

    return results

def _evaluate_switch_actions(state: BattleState) -> List[dict]:
    results: List[dict] = []

    for target in state.available_switches:
        species = target.species or "Unknown switch target"
        score, notes = _score_switch(
            target,
            state.defender,
            state.field.attacker_side,
        )

        results.append(
            {
                "actionType": "switch",
                "name": species,
                "moveType": None,
                "moveCategory": None,
                "basePower": None,
                "typeMultiplier": None,
                "minDamage": None,
                "maxDamage": None,
                "minDamagePercent": None,
                "maxDamagePercent": None,
                "score": score,
                "confidence": 0.0,
                "notes": notes,
            }
        )

    return results



def evaluate_battle_state(
    state: BattleState,
    temperature: float = 8.0,
) -> Tuple[str, float, List[dict], str, List[str]]:
    results: List[dict] = []
    raw_scores: Dict[str, float] = {}

    assumptions_used: List[str] = [
        f"Format context placeholder: Gen {state.generation} / {state.format_name}.",
        "Current evaluator is shallow and mostly single-turn.",
        "Only relevant offensive/defensive stat boosts are currently applied.",
    ]
    assumptions_used.extend(_field_assumptions(state.field))

    results.extend(_evaluate_move_actions(state))
    results.extend(_evaluate_switch_actions(state))

    for action in results:
        raw_scores[f"{action['actionType']}::{action['name']}"] = action["score"]

    confidences = _softmax(raw_scores, temperature=temperature)

    for action in results:
        action["confidence"] = confidences.get(f"{action['actionType']}::{action['name']}", 0.0)

    results.sort(key=lambda x: x["score"], reverse=True)

    best_action = results[0]["name"]
    best_conf = results[0]["confidence"]
    top = results[0]

    if top["actionType"] == "move":
        explanation = (
            f"Recommended action: use {best_action}. "
            f"It currently scores highest "
            f"({top['minDamagePercent']:.1f}–{top['maxDamagePercent']:.1f}% estimated damage, "
            f"{top['typeMultiplier']}x effectiveness)."
        )
    else:
        explanation = (
            f"Recommended action: switch to {best_action}. "
            f"It currently scores highest based on defensive matchup and board-position heuristics."
        )

    return best_action, best_conf, results, explanation, assumptions_used


def evaluate_manual_inputs(
    attacker: CombatantInfo,
    defender: CombatantInfo,
    moves: List[MoveInfo],
    temperature: float = 8.0,
) -> Tuple[str, float, List[dict], str]:
    state = BattleState(
        attacker=ActivePokemon(
            species=None,
            types=list(attacker.types),
            atk=float(attacker.atk or 100),
            def_=float(attacker.def_ or 100),
            spa=float(attacker.spa or 100),
            spd=float(attacker.spd or 100),
            spe=100.0,
            hp=float(attacker.hp or 100),
            level=attacker.level,
            burned=bool(attacker.burned),
            tera_active=bool(attacker.tera_active),
            current_hp=float(attacker.hp or 100),
            status="brn" if attacker.burned else None,
            boosts=StatBoosts(),
        ),
        defender=ActivePokemon(
            species=None,
            types=list(defender.types),
            atk=float(defender.atk or 100),
            def_=float(defender.def_ or 100),
            spa=float(defender.spa or 100),
            spd=float(defender.spd or 100),
            spe=100.0,
            hp=float(defender.hp or 100),
            level=defender.level,
            burned=bool(defender.burned),
            tera_active=bool(defender.tera_active),
            current_hp=float(defender.hp or 100),
            status="brn" if defender.burned else None,
            boosts=StatBoosts(),
        ),
        moves=list(moves),
        available_switches=[],
        field=FieldState(
            attacker_side=SideHazards(),
            defender_side=SideHazards(),
        ),
        generation=9,
        format_name="legacy-suggest-move",
    )

    best_action, conf, ranked, explanation, _ = evaluate_battle_state(
        state=state,
        temperature=temperature,
    )

    move_only = [r for r in ranked if r["actionType"] == "move"]
    if not move_only:
        return best_action, conf, ranked, explanation

    return best_action, conf, move_only, explanation
