from app.domain.battle_state import PokemonState, SideConditions, StatBoosts
from app.engine.switch_engine import score_switch


def make_pokemon(
    species: str,
    types: list[str],
    hp: int = 100,
    current_hp: int = 100,
    spe: int = 100,
):
    return PokemonState(
        species=species,
        types=types,
        atk=100,
        def_=100,
        spa=100,
        spd=100,
        spe=spe,
        hp=hp,
        current_hp=current_hp,
        boosts=StatBoosts(),
    )


def test_hazard_taxed_switch_is_penalized_more_heavily():
    dragonite = make_pokemon(
        species="Dragonite",
        types=["Dragon", "Flying"],
        hp=100,
        current_hp=50,
        spe=80,
    )
    great_tusk = make_pokemon(
        species="Great Tusk",
        types=["Ground", "Fighting"],
        hp=115,
        current_hp=115,
        spe=87,
    )

    no_hazards_score, _ = score_switch(
        switch_target=dragonite,
        opposing_active=great_tusk,
        entry_side_conditions=SideConditions(),
    )
    stealth_rock_score, notes = score_switch(
        switch_target=dragonite,
        opposing_active=great_tusk,
        entry_side_conditions=SideConditions(stealth_rock=True),
    )

    assert stealth_rock_score < no_hazards_score
    assert any("hazard" in note.lower() or "entry" in note.lower() for note in notes)