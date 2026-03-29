from __future__ import annotations

import json
from typing import Any, Dict

from app.providers.provider_utils import POKEMON_PATH
from app.services.name_normalize import normalize_key

_pokemon_cache: Dict[str, Any] | None = None
_pokemon_index: Dict[str, str] | None = None


def load_pokemon_data() -> Dict[str, Any]:
    global _pokemon_cache, _pokemon_index

    if _pokemon_cache is None:
        with open(POKEMON_PATH, "r", encoding="utf-8") as f:
            _pokemon_cache = json.load(f)

        _pokemon_index = {
            normalize_key(name): name
            for name in _pokemon_cache.keys()
        }

    return _pokemon_cache


def get_pokemon_index() -> Dict[str, str]:
    load_pokemon_data()
    assert _pokemon_index is not None
    return _pokemon_index


def resolve_pokemon_name(name: str) -> str | None:
    index = get_pokemon_index()
    return index.get(normalize_key(name))