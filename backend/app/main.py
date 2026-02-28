from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from app.schemas.type_effectiveness import TypeEffectivenessRequest, TypeEffectivenessResponse
from app.services.type_effectiveness import combined_multiplier
from app.schemas.damage_preview import DamagePreviewRequest, DamagePreviewResponse
from app.services.damage_preview import estimate_damage
from app.schemas.suggest_move import SuggestMoveRequest, SuggestMoveResponse
from app.services.suggest_move import suggest_move
from fastapi import Query
from app.services.data_loader import (
    load_pokemon_data,
    load_moves_data,
    resolve_pokemon_name,
    resolve_move_name,
    search_keys,
    get_pokemon_index,
    get_moves_index,
)
from app.schemas.data_endpoints import (
    SearchListResponse,
    PokemonDetailResponse,
    MoveDetailResponse,
)

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

# suggest move endpoint
from app.schemas.suggest_move import SuggestMoveRequest, SuggestMoveResponse
from app.services.suggest_move import suggest_move

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

# pokemon and moves endpoints
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
    }