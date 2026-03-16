from app.domain.battle_state import (
    ActivePokemon,
    BattleState,
    FieldState,
    SideHazards,
    StatBoosts,
)
from app.schemas.battle_state import BattleStateRequest


def _to_domain_pokemon(pokemon) -> ActivePokemon:
    status = getattr(pokemon, "status", None)
    burned = bool(getattr(pokemon, "burned", False) or status == "brn")

    return ActivePokemon(
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
        current_hp=float(pokemon.currentHp) if getattr(pokemon, "currentHp", None) is not None else None,
        status=status,
        boosts=StatBoosts(
            atk=getattr(getattr(pokemon, "boosts", None), "atk", 0),
            def_=getattr(getattr(pokemon, "boosts", None), "def_", 0),
            spa=getattr(getattr(pokemon, "boosts", None), "spa", 0),
            spd=getattr(getattr(pokemon, "boosts", None), "spd", 0),
            spe=getattr(getattr(pokemon, "boosts", None), "spe", 0),
        ),
    )


def to_domain_battle_state(payload: BattleStateRequest) -> BattleState:
    return BattleState(
        attacker=_to_domain_pokemon(payload.attacker),
        defender=_to_domain_pokemon(payload.defender),
        moves=list(payload.moves),
        available_switches=[_to_domain_pokemon(p) for p in payload.availableSwitches],
        field=FieldState(
            weather=payload.field.weather,
            terrain=payload.field.terrain,
            attacker_side=SideHazards(
                stealth_rock=payload.field.attacker_side.stealth_rock,
                spikes_layers=payload.field.attacker_side.spikes_layers,
                sticky_web=payload.field.attacker_side.sticky_web,
                toxic_spikes_layers=payload.field.attacker_side.toxic_spikes_layers,
            ),
            defender_side=SideHazards(
                stealth_rock=payload.field.defender_side.stealth_rock,
                spikes_layers=payload.field.defender_side.spikes_layers,
                sticky_web=payload.field.defender_side.sticky_web,
                toxic_spikes_layers=payload.field.defender_side.toxic_spikes_layers,
            ),
        ),
        generation=payload.generation,
        format_name=payload.formatName or "manual",
    )
