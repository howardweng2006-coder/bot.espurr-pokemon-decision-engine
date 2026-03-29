from fastapi import APIRouter

from app.adapters.manual_input_adapter import to_domain_battle_state
from app.engine.damage_engine import estimate_damage
from app.engine.evaluation_engine import evaluate_battle_state
from app.schemas.battle_state import BattleStateRequest, EvaluatePositionResponse
from app.schemas.damage_preview import DamagePreviewRequest, DamagePreviewResponse

router = APIRouter()


@router.post("/damage-preview", response_model=DamagePreviewResponse)
def damage_preview(payload: DamagePreviewRequest):
    result = estimate_damage(
        attacker=payload.attacker,
        defender=payload.defender,
        move=payload.move,
    )

    return {
        "moveType": payload.move.type,
        "moveCategory": payload.move.category,
        "basePower": payload.move.power or 0,
        "stab": result["stab"],
        "typeMultiplier": result["typeMultiplier"],
        "minDamage": result["minDamage"],
        "maxDamage": result["maxDamage"],
        "minDamagePercent": result["minPercent"],
        "maxDamagePercent": result["maxPercent"],
        "level": result["level"],
        "critApplied": result["critApplied"],
        "burnApplied": result["burnApplied"],
        "notes": result["notes"],
    }


@router.post("/evaluate-position", response_model=EvaluatePositionResponse)
def evaluate_position(payload: BattleStateRequest):
    state = to_domain_battle_state(payload)

    best_action, conf, ranked, explanation, assumptions_used = evaluate_battle_state(
        state=state,
    )

    return {
        "bestAction": best_action,
        "confidence": conf,
        "rankedActions": ranked,
        "explanation": explanation,
        "assumptionsUsed": assumptions_used,
    }