from fastapi import APIRouter, HTTPException

from app.engine.type_engine import combined_multiplier
from app.providers.type_chart_provider import load_type_chart
from app.schemas.type_effectiveness import (
    TypeEffectivenessRequest,
    TypeEffectivenessResponse,
)

router = APIRouter()


@router.post("/type-effectiveness", response_model=TypeEffectivenessResponse)
def type_effectiveness(payload: TypeEffectivenessRequest):
    try:
        mult, breakdown = combined_multiplier(payload.moveType, payload.defenderTypes)
        return {
            "moveType": payload.moveType,
            "defenderTypes": payload.defenderTypes,
            "multiplier": mult,
            "breakdown": breakdown,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/types")
def get_types():
    chart = load_type_chart()
    return {"types": sorted(chart.keys())}