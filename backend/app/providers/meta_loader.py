from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from app.inference.models import MetaPriorSnapshot
from app.providers.meta_normalizer import snapshot_from_dict


def default_meta_base_dir() -> Path:
    return Path(__file__).resolve().parent.parent / "data" / "meta"


def snapshot_path_for_query(
    *,
    base_dir: Path,
    format_id: str,
    rating_bucket: str,
    month_window: int,
) -> Path:
    filename = f"rolling_{month_window}m.json"
    return base_dir / format_id / rating_bucket / filename


def load_snapshot_from_disk(
    *,
    base_dir: Path,
    format_id: str,
    generation: int,
    rating_bucket: str,
    month_window: int,
) -> Optional[MetaPriorSnapshot]:
    path = snapshot_path_for_query(
        base_dir=base_dir,
        format_id=format_id,
        rating_bucket=rating_bucket,
        month_window=month_window,
    )

    if not path.exists():
        return None

    payload = json.loads(path.read_text(encoding="utf-8"))
    snapshot = snapshot_from_dict(payload)

    # Defensive check so bad files fail soft instead of poisoning provider behavior.
    if snapshot.format_id != format_id or snapshot.generation != generation:
        return None

    return snapshot