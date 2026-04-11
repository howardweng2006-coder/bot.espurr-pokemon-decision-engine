import json
from pathlib import Path

import pytest

from app.adapters.manual_input_adapter import to_domain_battle_state
from app.engine.evaluation_engine import evaluate_battle_state
from app.schemas.battle_state import BattleStateRequest


FIXTURE_DIR = Path(__file__).parent / "fixtures"


def load_fixture(name: str) -> BattleStateRequest:
    path = FIXTURE_DIR / name
    with path.open("r", encoding="utf-8") as f:
        payload = json.load(f)
    return BattleStateRequest.model_validate(payload)


def evaluate_fixture(name: str):
    request = load_fixture(name)
    state = to_domain_battle_state(request)
    best_action, confidence, ranked_actions, explanation, assumptions = evaluate_battle_state(state)

    return {
        "best_action": best_action,
        "confidence": confidence,
        "ranked_actions": ranked_actions,
        "explanation": explanation,
        "assumptions": assumptions,
    }


def action_key(action: dict) -> str:
    return f"{action['actionType']}::{action['name']}"


def top_keys(result: dict, n: int = 3) -> list[str]:
    return [action_key(action) for action in result["ranked_actions"][:n]]


def top_action(result: dict) -> dict:
    return result["ranked_actions"][0]


def assert_top_1(result: dict, expected_key: str):
    actual = action_key(top_action(result))
    assert actual == expected_key, (
        f"Expected top action {expected_key}, got {actual}. "
        f"Top 3: {top_keys(result, 3)}"
    )


def assert_in_top_n(result: dict, expected_key: str, n: int):
    keys = top_keys(result, n)
    assert expected_key in keys, (
        f"Expected {expected_key} in top {n}, got {keys}"
    )


def assert_not_top_1(result: dict, banned_key: str):
    actual = action_key(top_action(result))
    assert actual != banned_key, (
        f"Did not expect {banned_key} to be top 1. Top 3: {top_keys(result, 3)}"
    )


def assert_action_type_present(result: dict, action_type: str):
    action_types = {action["actionType"] for action in result["ranked_actions"]}
    assert action_type in action_types


def assert_explanation_mentions_any(result: dict, phrases: list[str]):
    explanation = result["explanation"].lower()
    assert any(phrase.lower() in explanation for phrase in phrases), (
        f"Expected explanation to mention one of {phrases!r}. "
        f"Actual explanation: {result['explanation']}"
    )


# -------------------------
# Baseline regression pack
# -------------------------

@pytest.mark.parametrize(
    "fixture_name, expected_top_1, banned_top_1",
    [
        (
            "electric_into_gyarados_ko.json",
            "move::Thunderbolt",
            "switch::Ferrothorn",
        ),
        (
            "priority_picks_off_faster_target.json",
            "move::Extreme Speed",
            "move::Earthquake",
        ),
    ],
)
def test_baseline_top_1_scenarios(fixture_name: str, expected_top_1: str, banned_top_1: str):
    result = evaluate_fixture(fixture_name)

    assert_action_type_present(result, "move")
    assert_action_type_present(result, "switch")
    assert_top_1(result, expected_top_1)
    assert_not_top_1(result, banned_top_1)
    assert 0.0 <= result["confidence"] <= 1.0
    assert isinstance(result["assumptions"], list)
    assert isinstance(result["explanation"], str) and len(result["explanation"]) > 0


def test_hazard_penalty_discourages_bad_switch():
    result = evaluate_fixture("hazard_switch_penalty_dragonite.json")

    # This one is intentionally a little softer because exact top-1 may move
    # around as response modeling changes. The important regression is that
    # the hazard-punished Dragonite switch should not become the best action.
    assert_action_type_present(result, "move")
    assert_action_type_present(result, "switch")
    assert_in_top_n(result, "move::Hydro Pump", 2)
    assert_not_top_1(result, "switch::Dragonite")


def test_levitate_immunity_discourages_ground_spam():
    result = evaluate_fixture("levitate_immunity_respect.json")

    assert_action_type_present(result, "move")
    assert_action_type_present(result, "switch")
    assert_not_top_1(result, "move::Headlong Rush")

    safe_top_two = set(top_keys(result, 2))
    assert any(
        key in safe_top_two
        for key in ["move::Knock Off", "move::Close Combat", "switch::Kingambit"]
    ), f"Expected a safe non-Ground line in top 2, got {top_keys(result, 3)}"

# ----------------------------------
# Aspirational competitive scenarios
# ----------------------------------
# These are intentionally marked xfail because they align with known weak /
# missing reasoning layers in the current engine: setup value, hazard-control
# value, and long-horizon preservation logic.

@pytest.mark.xfail(reason="Setup value is still weak / not first-class modeled.")
def test_forced_switch_setup_window_volcarona():
    result = evaluate_fixture("forced_switch_setup_volcarona.json")

    assert_in_top_n(result, "move::Quiver Dance", 2)
    assert_not_top_1(result, "move::Flamethrower")


@pytest.mark.xfail(reason="Hazard-control value is not yet a strong modeled concept.")
def test_hazard_control_should_be_competitively_rewarded():
    result = evaluate_fixture("hazard_control_defog_corviknight.json")

    assert_in_top_n(result, "move::Defog", 2)
    assert_not_top_1(result, "move::Body Press")


@pytest.mark.xfail(reason="Preservation / sack logic is not yet implemented.")
def test_preserve_endgame_check_over_short_term_trade():
    result = evaluate_fixture("preserve_lando_for_gambit_endgame.json")

    assert_in_top_n(result, "switch::Toxapex", 2)
    assert_not_top_1(result, "switch::Landorus-Therian")