from __future__ import annotations

import json
from typing import Any, Dict

from app.providers.provider_utils import DATA_DIR

TYPE_CHART_PATH = DATA_DIR / "typeChart.json"

_type_chart_cache: Dict[str, Any] | None = None


def load_type_chart() -> Dict[str, Any]:
    global _type_chart_cache

    if _type_chart_cache is None:
        with open(TYPE_CHART_PATH, "r", encoding="utf-8") as f:
            _type_chart_cache = json.load(f)

    return _type_chart_cache