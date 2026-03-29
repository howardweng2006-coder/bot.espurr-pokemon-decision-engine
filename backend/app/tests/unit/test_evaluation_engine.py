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
    )


def make_state():
    my_active = make_pokemon(species="Pikachu", types=["Electric"], spa=110, spe=120)
    opponent_active = make_pokemon(species="Gyarados", types=["Water", "Flying"], spd=95, hp=100)
    switch_target = make_pokemon(species="Ferrothorn", types=["Grass", "Steel"], hp=100, current_hp=100)

    moves = [
        DummyMove(name="Thunderbolt", move_type="Electric", power=90, category="special"),
        DummyMove(name="Quick Attack", move_type="Normal", power=40, category="physical", priority=1),
    ]

    return BattleState(
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


def test_returns_both_move_and_switch_actions():
    state = make_state()

    best_action, confidence, ranked_actions, explanation, assumptions = evaluate_battle_state(state)

    action_types = {action["actionType"] for action in ranked_actions}

    assert "move" in action_types
    assert "switch" in action_types
    assert len(ranked_actions) == 3
    assert isinstance(explanation, str) and len(explanation) > 0
    assert isinstance(assumptions, list) and len(assumptions) > 0
    assert 0.0 <= confidence <= 1.0


def test_best_action_is_top_scored():
    state = make_state()

    best_action, confidence, ranked_actions, explanation, assumptions = evaluate_battle_state(state)

    assert ranked_actions[0]["name"] == best_action
    assert ranked_actions[0]["confidence"] == confidence

    scores = [action["score"] for action in ranked_actions]
    assert scores == sorted(scores, reverse=True)