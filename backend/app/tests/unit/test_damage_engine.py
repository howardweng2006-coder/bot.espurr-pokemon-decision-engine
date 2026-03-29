from app.domain.battle_state import PokemonState, StatBoosts
from app.engine.damage_engine import estimate_damage


class DummyMove:
    def __init__(
        self,
        name: str,
        move_type: str,
        power: int,
        category: str,
        priority: int = 0,
        crit: bool = False,
        level: int | None = None,
    ):
        self.name = name
        self.type = move_type
        self.power = power
        self.category = category
        self.priority = priority
        self.crit = crit
        self.level = level


def make_pokemon(
    types,
    atk=100,
    def_=100,
    spa=100,
    spd=100,
    spe=100,
    hp=100,
    level=50,
    burned=False,
    tera_active=False,
):
    return PokemonState(
        species="Testmon",
        types=types,
        atk=atk,
        def_=def_,
        spa=spa,
        spd=spd,
        spe=spe,
        hp=hp,
        level=level,
        burned=burned,
        tera_active=tera_active,
        current_hp=hp,
        status="brn" if burned else None,
        boosts=StatBoosts(),
    )


def test_status_move_zero_damage():
    attacker = make_pokemon(["Psychic"])
    defender = make_pokemon(["Water"])
    move = DummyMove(name="Calm Mind", move_type="Psychic", power=0, category="status")

    result = estimate_damage(attacker=attacker, defender=defender, move=move)

    assert result["minDamage"] == 0.0
    assert result["maxDamage"] == 0.0
    assert result["minPercent"] == 0.0
    assert result["maxPercent"] == 0.0


def test_stab_increases_damage():
    attacker_with_stab = make_pokemon(["Fire"], spa=120)
    attacker_without_stab = make_pokemon(["Water"], spa=120)
    defender = make_pokemon(["Grass"], spd=100, hp=100)
    move = DummyMove(name="Flamethrower", move_type="Fire", power=90, category="special")

    result_with_stab = estimate_damage(
        attacker=attacker_with_stab,
        defender=defender,
        move=move,
    )
    result_without_stab = estimate_damage(
        attacker=attacker_without_stab,
        defender=defender,
        move=move,
    )

    assert result_with_stab["minDamage"] > result_without_stab["minDamage"]
    assert result_with_stab["maxDamage"] > result_without_stab["maxDamage"]