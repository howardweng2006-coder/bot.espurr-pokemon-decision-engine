import json
from pathlib import Path
from typing import Any, Dict, List

from app.services.name_normalize import normalize_key

DATA_DIR = Path(__file__).resolve().parents[2] / "data"
POKEMON_PATH = DATA_DIR / "pokemon.json"
MOVES_PATH = DATA_DIR / "moves.json"

_pokemon_cache: Dict[str, Any] | None = None
_moves_cache: Dict[str, Any] | None = None

_pokemon_index: Dict[str, str] | None = None
_moves_index: Dict[str, str] | None = None


# -------------------------
# Loaders
# -------------------------

def load_pokemon_data() -> Dict[str, Any]:
    global _pokemon_cache, _pokemon_index
    if _pokemon_cache is None:
        with open(POKEMON_PATH, "r", encoding="utf-8") as f:
            _pokemon_cache = json.load(f)

        # build normalized lookup index
        _pokemon_index = {
            normalize_key(name): name
            for name in _pokemon_cache.keys()
        }

    return _pokemon_cache


def load_moves_data() -> Dict[str, Any]:
    global _moves_cache, _moves_index
    if _moves_cache is None:
        with open(MOVES_PATH, "r", encoding="utf-8") as f:
            _moves_cache = json.load(f)

        _moves_index = {
            normalize_key(name): name
            for name in _moves_cache.keys()
        }

    return _moves_cache


# -------------------------
# Index accessors (clean API)
# -------------------------

def get_pokemon_index() -> Dict[str, str]:
    load_pokemon_data()
    assert _pokemon_index is not None
    return _pokemon_index


def get_moves_index() -> Dict[str, str]:
    load_moves_data()
    assert _moves_index is not None
    return _moves_index


# -------------------------
# Name resolution
# -------------------------

def resolve_pokemon_name(name: str) -> str | None:
    index = get_pokemon_index()
    return index.get(normalize_key(name))


def resolve_move_name(name: str) -> str | None:
    index = get_moves_index()
    return index.get(normalize_key(name))


# -------------------------
# Search helper
# -------------------------

def search_keys(index: Dict[str, str], query: str, limit: int = 10) -> List[str]:
    """
    Simple search:
    - startswith prioritized
    - substring match second
    - sorted for deterministic UX
    """
    q = normalize_key(query)
    if not q:
        return []

    starts = []
    contains = []

    for norm, canonical in index.items():
        if norm.startswith(q):
            starts.append(canonical)
        elif q in norm:
            contains.append(canonical)

    starts.sort()
    contains.sort()

    return (starts + contains)[:limit]