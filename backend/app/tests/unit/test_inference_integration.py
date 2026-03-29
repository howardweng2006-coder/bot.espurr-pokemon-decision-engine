from app.domain.battle_state import (
    BattleState,
    FieldState,
    FormatContext,
    PokemonState,
    SideConditions,
    SideState,
    StatBoosts,
)
from app.engine.evaluation_engine import evaluate_battle_state


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
    species: str,
    types,
    atk=100,
    def_=100,
    spa=100,
    spd=100,
    spe=100,
    hp=100,
    current_hp=100,
    revealed_moves=None,
):
    return PokemonState(
        species=species,
        types=types,
        atk=atk,
        def_=def_,
        spa=spa,
        spd=spd,
        spe=spe,
        hp=hp,
        level=50,
        burned=False,
        tera_active=False,
        current_hp=current_hp,
        status=None,
        boosts=StatBoosts(),
        revealed_moves=revealed_moves or [],
    )


def test_evaluation_includes_inference_assumptions_and_summary():
    my_active = make_pokemon(species="Pikachu", types=["Electric"], spa=110, spe=120)
    opponent_active = make_pokemon(
        species="Gyarados",
        types=["Water", "Flying"],
        spd=95,
        hp=100,
        revealed_moves=["Waterfall"],
    )
    switch_target = make_pokemon(species="Ferrothorn", types=["Grass", "Steel"], hp=100, current_hp=100)

    moves = [
        DummyMove(name="Thunderbolt", move_type="Electric", power=90, category="special"),
        DummyMove(name="Quick Attack", move_type="Normal", power=40, category="physical", priority=1),
    ]

    state = BattleState(
        my_side=SideState(
            active=my_active,
            bench=[switch_target],
            side_conditions=SideConditions(),
        ),
        opponent_side=SideState(
            active=opponent_active,
            bench=[],
            side_conditions=SideConditions(),
        ),
        moves=moves,
        field=FieldState(),
        format_context=FormatContext(
            generation=9,
            format_name="Gen 9 OU",
        ),
    )

    best_action, confidence, ranked_actions, explanation, assumptions = evaluate_battle_state(state)

    assert "Opponent active inference" in explanation
    assert any("Inference confidence" in assumption for assumption in assumptions)
    assert any("placeholder" in assumption.lower() for assumption in assumptions)