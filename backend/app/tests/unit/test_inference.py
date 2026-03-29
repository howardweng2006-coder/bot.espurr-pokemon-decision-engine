from app.domain.battle_state import PokemonState, StatBoosts
from app.inference.belief_updater import apply_revealed_move
from app.inference.set_inference import infer_pokemon_state


def make_pokemon(species: str | None, types):
    return PokemonState(
        species=species,
        types=types,
        atk=100,
        def_=100,
        spa=100,
        spd=100,
        spe=100,
        hp=100,
        level=50,
        burned=False,
        tera_active=False,
        current_hp=100,
        status=None,
        boosts=StatBoosts(),
    )


def test_infer_pokemon_state_returns_placeholder_candidate():
    pokemon = make_pokemon("Garchomp", ["Dragon", "Ground"])
    result = infer_pokemon_state(pokemon)

    assert result.species == "Garchomp"
    assert len(result.candidates) == 1
    assert result.candidates[0].label == "generic-placeholder-set"


def test_apply_revealed_move_adds_move_to_candidates():
    pokemon = make_pokemon("Garchomp", ["Dragon", "Ground"])
    inference = infer_pokemon_state(pokemon)

    updated = apply_revealed_move(inference, "Earthquake")

    assert "Earthquake" in updated.candidates[0].moves
    assert any("revealed move" in note for note in updated.notes)