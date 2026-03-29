import json
from pathlib import Path

from app.adapters.manual_input_adapter import to_domain_battle_state
from app.engine.evaluation_engine import evaluate_battle_state
from app.schemas.battle_state import BattleStateRequest


FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"


def load_fixture(name: str) -> BattleStateRequest:
    with open(FIXTURES_DIR / name, "r", encoding="utf-8") as f:
        data = json.load(f)
    return BattleStateRequest.model_validate(data)


def test_electric_into_gyarados_prefers_thunderbolt():
    payload = load_fixture("electric_into_gyarados.json")
    state = to_domain_battle_state(payload)

    best_action, confidence, ranked_actions, explanation, assumptions = evaluate_battle_state(state)

    assert best_action == "Thunderbolt"
    assert ranked_actions[0]["actionType"] == "move"
    assert ranked_actions[0]["name"] == "Thunderbolt"
    assert "Recommended action" in explanation
    assert any("Inference confidence" in assumption for assumption in assumptions)

def test_hazard_switch_penalty_prefers_safe_switch():
    payload = load_fixture("hazard_switch_penalty.json")
    state = to_domain_battle_state(payload)

    _, _, ranked, _, _ = evaluate_battle_state(state)

    switches = [a for a in ranked if a["actionType"] == "switch"]

    assert len(switches) >= 2
    assert switches[0]["name"] != "Volcarona"  # should avoid 4x SR weakness

def test_priority_move_beats_faster_opponent():
    payload = load_fixture("priority_vs_speed.json")
    state = to_domain_battle_state(payload)

    best_action, _, _, _, _ = evaluate_battle_state(state)

    assert best_action == "Bullet Punch"

def test_damage_preferred_over_status_in_simple_case():
    payload = load_fixture("status_vs_damage.json")
    state = to_domain_battle_state(payload)

    best_action, _, _, _, _ = evaluate_battle_state(state)

    assert best_action == "Shadow Ball"

def test_inference_notes_present():
    payload = load_fixture("inference_visible.json")
    state = to_domain_battle_state(payload)

    _, _, _, _, assumptions = evaluate_battle_state(state)

    assert any("Inference" in note for note in assumptions)