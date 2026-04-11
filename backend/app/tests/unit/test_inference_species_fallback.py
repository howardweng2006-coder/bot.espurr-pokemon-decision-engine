from app.domain.battle_state import PokemonState, StatBoosts
from app.inference.set_inference import infer_pokemon_state


def test_rotom_wash_species_fallback_infers_levitate():
    pokemon = PokemonState(
        species="Rotom-Wash",
        types=["Electric", "Water"],
        atk=65,
        def_=107,
        spa=105,
        spd=107,
        spe=86,
        hp=100,
        current_hp=100,
        boosts=StatBoosts(),
        revealed_moves=["Hydro Pump", "Volt Switch"],
    )

    result = infer_pokemon_state(pokemon)

    assert result.candidates
    candidate = result.candidates[0]
    assert candidate.ability == "Levitate"
    assert "Hydro Pump" in candidate.moves
    assert "Volt Switch" in candidate.moves
    assert result.confidence_label == "species-fallback"