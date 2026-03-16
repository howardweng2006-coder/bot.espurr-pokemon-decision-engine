from fastapi import FastAPI, HTTPException, Query
import app.services.battle_state_service as battle_state_service_module
import inspect
from fastapi.middleware.cors import CORSMiddleware

from app.adapters.manual_input_adapter import to_domain_battle_state
from app.schemas.battle_state import BattleStateRequest, EvaluatePositionResponse
from app.schemas.damage_preview import DamagePreviewRequest, DamagePreviewResponse
from app.schemas.data_endpoints import (
    MoveDetailResponse,
    PokemonDetailResponse,
    SearchListResponse,
)
from app.schemas.suggest_move import SuggestMoveRequest, SuggestMoveResponse
from app.schemas.type_effectiveness import (
    TypeEffectivenessRequest,
    TypeEffectivenessResponse,
)
from app.services.battle_state_service import evaluate_battle_state
from app.services.damage_preview import estimate_damage
from app.services.data_loader import (
    get_moves_index,
    get_pokemon_index,
    load_moves_data,
    load_pokemon_data,
    resolve_move_name,
    resolve_pokemon_name,
    search_keys,
)
from app.services.suggest_move import suggest_move
from app.services.type_effectiveness import combined_multiplier, load_type_chart

app = FastAPI(title="Pokemon Decision Engine API")

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


@app.post("/type-effectiveness", response_model=TypeEffectivenessResponse)
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

@app.get("/types")
def get_types():
    chart = load_type_chart()
    return {"types": sorted(chart.keys())}


@app.post("/damage-preview", response_model=DamagePreviewResponse)
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


@app.post("/suggest-move", response_model=SuggestMoveResponse)
def suggest_move_endpoint(payload: SuggestMoveRequest):
    best_move, conf, ranked, explanation = suggest_move(
        attacker=payload.attacker,
        defender=payload.defender,
        moves=payload.moves,
    )

    return {
        "bestMove": best_move,
        "confidence": conf,
        "rankedMoves": ranked,
        "explanation": explanation,
    }


@app.post("/evaluate-position", response_model=EvaluatePositionResponse)
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

@app.get("/pokemon", response_model=SearchListResponse)
def search_pokemon(search: str = Query(default="", min_length=1), limit: int = 10):
    index = get_pokemon_index()
    results = search_keys(index, search, limit=limit)
    return {"results": results}


@app.get("/pokemon/{name}", response_model=PokemonDetailResponse)
def get_pokemon(name: str):
    data = load_pokemon_data()
    canonical = resolve_pokemon_name(name)
    if not canonical:
        raise HTTPException(status_code=404, detail=f"Unknown Pokémon: {name}")

    entry = data[canonical]
    return {
        "name": canonical,
        "types": entry["types"],
        "base": entry["base"],
    }


@app.get("/moves", response_model=SearchListResponse)
def search_moves(search: str = Query(default="", min_length=1), limit: int = 10):
    index = get_moves_index()
    results = search_keys(index, search, limit=limit)
    return {"results": results}


@app.get("/moves/{name}", response_model=MoveDetailResponse)
def get_move(name: str):
    data = load_moves_data()
    canonical = resolve_move_name(name)
    if not canonical:
        raise HTTPException(status_code=404, detail=f"Unknown move: {name}")

    entry = data[canonical]
    return {
        "name": canonical,
        "type": entry["type"],
        "category": entry["category"],
        "power": int(entry.get("power", 0) or 0),
        "priority": int(entry.get("priority", 0) or 0),
    }