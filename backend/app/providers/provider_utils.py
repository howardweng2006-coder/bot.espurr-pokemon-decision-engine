from __future__ import annotations

from pathlib import Path
from typing import Dict, List

from app.services.name_normalize import normalize_key

DATA_DIR = Path(__file__).resolve().parents[2] / "data"
POKEMON_PATH = DATA_DIR / "pokemon.json"
MOVES_PATH = DATA_DIR / "moves.json"


def search_keys(index: Dict[str, str], query: str, limit: int = 10) -> List[str]:
    q = normalize_key(query)
    if not q:
        return []

    starts: List[str] = []
    contains: List[str] = []

    for norm, canonical in index.items():
        if norm.startswith(q):
            starts.append(canonical)
        elif q in norm:
            contains.append(canonical)

    starts.sort()
    contains.sort()

    return (starts + contains)[:limit]