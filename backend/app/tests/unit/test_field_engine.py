from app.domain.battle_state import PokemonState, SideConditions, StatBoosts
from app.engine.field_engine import (
    hazard_on_entry_context,
    is_grounded,
    spikes_percent,
    stealth_rock_percent,
)


def make_pokemon(types, hp=100, current_hp=100):
    return PokemonState(
        species="Testmon",
        types=types,
        atk=100,
        def_=100,
        spa=100,
        spd=100,
        spe=100,
        hp=hp,
        current_hp=current_hp,
        level=50,
        burned=False,
        tera_active=False,
        status=None,
        boosts=StatBoosts(),
    )


def test_is_grounded_false_for_flying_type():
    mon = make_pokemon(["Flying"])
    assert is_grounded(mon) is False


def test_is_grounded_true_for_non_flying_type():
    mon = make_pokemon(["Water"])
    assert is_grounded(mon) is True


def test_stealth_rock_percent_fire_flying():
    mon = make_pokemon(["Fire", "Flying"])
    assert stealth_rock_percent(mon) == 50.0


def test_spikes_percent_flying_immune():
    mon = make_pokemon(["Flying"])
    assert spikes_percent(mon, 3) == 0.0


def test_hazard_on_entry_context_combines_rocks_and_spikes():
    mon = make_pokemon(["Fire"])
    side_conditions = SideConditions(
        stealth_rock=True,
        spikes_layers=1,
        sticky_web=False,
        toxic_spikes_layers=0,
    )

    context, notes = hazard_on_entry_context(mon, side_conditions)

    assert context["stealthRockPercent"] == 25.0
    assert context["spikesPercent"] == 12.5
    assert context["totalEntryPercent"] == 37.5
    assert len(notes) > 0