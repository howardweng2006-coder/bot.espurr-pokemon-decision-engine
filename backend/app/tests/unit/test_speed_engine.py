from app.domain.battle_state import PokemonState, StatBoosts
from app.engine.speed_engine import turn_order_context


class DummyMove:
    def __init__(self, name: str, move_type: str, power: int, category: str, priority: int = 0):
        self.name = name
        self.type = move_type
        self.power = power
        self.category = category
        self.priority = priority
        self.crit = False
        self.level = 50


def make_pokemon(types, spe=100):
    return PokemonState(
        species="Testmon",
        types=types,
        atk=100,
        def_=100,
        spa=100,
        spd=100,
        spe=spe,
        hp=100,
        level=50,
        burned=False,
        tera_active=False,
        current_hp=100,
        status=None,
        boosts=StatBoosts(),
    )


def test_priority_overrides_speed():
    attacking_pokemon = make_pokemon(["Normal"], spe=50)
    defending_pokemon = make_pokemon(["Normal"], spe=200)
    move = DummyMove(name="Quick Attack", move_type="Normal", power=40, category="physical", priority=1)

    order, notes = turn_order_context(
        attacking_pokemon=attacking_pokemon,
        defending_pokemon=defending_pokemon,
        move=move,
    )

    assert order == "attacker_first"
    assert any("Positive move priority applied" in note for note in notes)


def test_faster_mon_moves_first():
    attacking_pokemon = make_pokemon(["Electric"], spe=140)
    defending_pokemon = make_pokemon(["Water"], spe=90)
    move = DummyMove(name="Thunderbolt", move_type="Electric", power=90, category="special", priority=0)

    order, notes = turn_order_context(
        attacking_pokemon=attacking_pokemon,
        defending_pokemon=defending_pokemon,
        move=move,
    )

    assert order == "attacker_first"
    assert any("estimated to move first" in note for note in notes)