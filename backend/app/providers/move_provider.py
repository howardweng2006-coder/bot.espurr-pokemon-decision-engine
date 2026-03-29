from __future__ import annotations

import json
from typing import Any, Dict

from app.providers.provider_utils import MOVES_PATH
from app.services.name_normalize import normalize_key

_moves_cache: Dict[str, Any] | None = None
_moves_index: Dict[str, str] | None = None


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


def get_moves_index() -> Dict[str, str]:
    load_moves_data()
    assert _moves_index is not None
    return _moves_index


def resolve_move_name(name: str) -> str | None:
    index = get_moves_index()
    return index.get(normalize_key(name))