from fastapi import APIRouter, HTTPException, Query

from app.providers.move_provider import (
    get_moves_index,
    load_moves_data,
    resolve_move_name,
)
from app.providers.pokemon_provider import (
    get_pokemon_index,
    load_pokemon_data,
    resolve_pokemon_name,
)
from app.providers.provider_utils import search_keys
from app.schemas.data_endpoints import (
    MoveDetailResponse,
    PokemonDetailResponse,
    SearchListResponse,
)

router = APIRouter()


@router.get("/pokemon", response_model=SearchListResponse)
def search_pokemon(search: str = Query(default="", min_length=1), limit: int = 10):
    index = get_pokemon_index()
    results = search_keys(index, search, limit=limit)
    return {"results": results}


@router.get("/pokemon/{name}", response_model=PokemonDetailResponse)
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


@router.get("/moves", response_model=SearchListResponse)
def search_moves(search: str = Query(default="", min_length=1), limit: int = 10):
    index = get_moves_index()
    results = search_keys(index, search, limit=limit)
    return {"results": results}


@router.get("/moves/{name}", response_model=MoveDetailResponse)
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