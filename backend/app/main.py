from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from app.schemas.type_effectiveness import TypeEffectivenessRequest, TypeEffectivenessResponse
from app.services.type_effectiveness import combined_multiplier
from app.schemas.damage_preview import DamagePreviewRequest, DamagePreviewResponse
from app.services.damage_preview import estimate_damage

app = FastAPI(title="Pokemon Decision Engine API")

# CORS middleware, health and root routes

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/")
def root():
    return {"message": "Pokemon Decision Engine API. Go to /docs"}

# type effectiveness endpoint

@app.post("/type-effectiveness", response_model=TypeEffectivenessResponse)
def type_effectiveness(payload: TypeEffectivenessRequest):
    try:
        mult, breakdown = combined_multiplier(payload.moveType, payload.defenderTypes)
        return {
            "moveType": payload.moveType,
            "defenderTypes": payload.defenderTypes,
            "multiplier": mult,
            "breakdown": breakdown
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

# get /types endpoint to keep frontend from duplicating type lists. makes this api layer the
# source of truth.

from app.services.type_effectiveness import load_type_chart

@app.get("/types")
def get_types():
    chart = load_type_chart()
    # Keys are the attacking types; in the standard chart it's all 18 types.
    return {"types": sorted(chart.keys())}

# damage preview endpoint

@app.post("/damage-preview", response_model=DamagePreviewResponse)
def damage_preview(payload: DamagePreviewRequest):
    damage, damage_pct, stab, type_mult, notes = estimate_damage(
        attacker=payload.attacker,
        defender=payload.defender,
        move=payload.move,
    )

    return {
        "moveType": payload.move.type,
        "moveCategory": payload.move.category,
        "basePower": payload.move.power or 0,
        "stab": stab,
        "typeMultiplier": type_mult,
        "estimatedDamage": damage,
        "estimatedDamagePercent": damage_pct,
        "notes": notes,
    }