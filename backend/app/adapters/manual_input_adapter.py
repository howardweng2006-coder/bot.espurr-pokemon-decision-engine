from __future__ import annotations

from app.domain.battle_state import (
    BattleState,
    FieldState,
    FormatContext,
    PokemonState,
    SideConditions,
    SideState,
    StatBoosts,
)
from app.schemas.battle_state import BattleStateRequest


def _to_domain_pokemon(pokemon) -> PokemonState:
    status = getattr(pokemon, "status", None)
    burned = bool(getattr(pokemon, "burned", False) or status == "brn")

    current_hp = (
        float(pokemon.currentHp)
        if getattr(pokemon, "currentHp", None) is not None
        else None
    )

    return PokemonState(
        species=getattr(pokemon, "species", None),
        types=list(pokemon.types),
        atk=float(getattr(pokemon, "atk", 100) or 100),
        def_=float(getattr(pokemon, "def_", 100) or 100),
        spa=float(getattr(pokemon, "spa", 100) or 100),
        spd=float(getattr(pokemon, "spd", 100) or 100),
        spe=float(getattr(pokemon, "spe", 100) or 100),
        hp=float(getattr(pokemon, "hp", 100) or 100),
        level=getattr(pokemon, "level", None),
        burned=burned,
        tera_active=bool(getattr(pokemon, "tera_active", False)),
        current_hp=current_hp,
        status=status,
        boosts=StatBoosts(
            atk=getattr(getattr(pokemon, "boosts", None), "atk", 0),
            def_=getattr(getattr(pokemon, "boosts", None), "def_", 0),
            spa=getattr(getattr(pokemon, "boosts", None), "spa", 0),
            spd=getattr(getattr(pokemon, "boosts", None), "spd", 0),
            spe=getattr(getattr(pokemon, "boosts", None), "spe", 0),
        ),
        revealed_moves=list(getattr(pokemon, "revealedMoves", []) or []),
    )


def _to_domain_side(side) -> SideState:
    return SideState(
        active=_to_domain_pokemon(side.active),
        bench=[_to_domain_pokemon(pokemon) for pokemon in side.bench],
        side_conditions=SideConditions(
            stealth_rock=side.side_conditions.stealth_rock,
            spikes_layers=side.side_conditions.spikes_layers,
            sticky_web=side.side_conditions.sticky_web,
            toxic_spikes_layers=side.side_conditions.toxic_spikes_layers,
        ),
    )


def to_domain_battle_state(payload: BattleStateRequest) -> BattleState:
    return BattleState(
        my_side=_to_domain_side(payload.my_side),
        opponent_side=_to_domain_side(payload.opponent_side),
        moves=list(payload.moves),
        field=FieldState(
            weather=payload.field.weather,
            terrain=payload.field.terrain,
        ),
        format_context=FormatContext(
            generation=payload.format_context.generation,
            format_name=payload.format_context.formatName or "manual",
            ruleset=list(payload.format_context.ruleset),
        ),
    )