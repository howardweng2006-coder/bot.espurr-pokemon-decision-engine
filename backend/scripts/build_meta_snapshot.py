from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def _ensure_dir(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def _weighted_value(value: str, weight: float, notes: list[str] | None = None) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "value": value,
        "weight": float(weight),
    }
    if notes:
        payload["notes"] = notes
    return payload


def _weighted_spread(
    *,
    label: str,
    nature: str | None,
    evs: dict[str, int],
    ivs: dict[str, int] | None = None,
    weight: float,
    notes: list[str] | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "label": label,
        "nature": nature,
        "evs": evs,
        "ivs": ivs or {},
        "weight": float(weight),
    }
    if notes:
        payload["notes"] = notes
    return payload


def _normalize_species_prior(species_name: str, payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "species": species_name,
        "usage_weight": float(payload.get("usage_weight", 1.0)),
        "moves": [
            _weighted_value(entry["value"], entry["weight"], entry.get("notes"))
            for entry in payload.get("moves", [])
        ],
        "items": [
            _weighted_value(entry["value"], entry["weight"], entry.get("notes"))
            for entry in payload.get("items", [])
        ],
        "abilities": [
            _weighted_value(entry["value"], entry["weight"], entry.get("notes"))
            for entry in payload.get("abilities", [])
        ],
        "tera_types": [
            _weighted_value(entry["value"], entry["weight"], entry.get("notes"))
            for entry in payload.get("tera_types", [])
        ],
        "spreads": [
            _weighted_spread(
                label=entry["label"],
                nature=entry.get("nature"),
                evs=dict(entry.get("evs", {})),
                ivs=dict(entry.get("ivs", {})),
                weight=entry["weight"],
                notes=entry.get("notes"),
            )
            for entry in payload.get("spreads", [])
        ],
        "teammate_weights": [
            _weighted_value(entry["value"], entry["weight"], entry.get("notes"))
            for entry in payload.get("teammate_weights", [])
        ],
        "lead_weights": [
            _weighted_value(entry["value"], entry["weight"], entry.get("notes"))
            for entry in payload.get("lead_weights", [])
        ],
        "associations": {
            "move_move": list(payload.get("associations", {}).get("move_move", [])),
            "move_item": list(payload.get("associations", {}).get("move_item", [])),
            "move_ability": list(payload.get("associations", {}).get("move_ability", [])),
            "move_tera": list(payload.get("associations", {}).get("move_tera", [])),
            "item_ability": list(payload.get("associations", {}).get("item_ability", [])),
            "item_spread": list(payload.get("associations", {}).get("item_spread", [])),
            "ability_tera": list(payload.get("associations", {}).get("ability_tera", [])),
        },
        "notes": list(payload.get("notes", [])),
    }


def build_snapshot(raw_payload: dict[str, Any]) -> dict[str, Any]:
    format_id = str(raw_payload["format_id"])
    generation = int(raw_payload["generation"])
    rating_bucket = str(raw_payload["rating_bucket"])
    month_window = list(raw_payload["month_window"])

    raw_species = dict(raw_payload.get("species_priors", {}))
    normalized_species = {
        species_name: _normalize_species_prior(species_name, species_payload)
        for species_name, species_payload in raw_species.items()
    }

    return {
        "format_id": format_id,
        "generation": generation,
        "rating_bucket": rating_bucket,
        "month_window": month_window,
        "species_priors": normalized_species,
        "notes": list(raw_payload.get("notes", [])),
    }


def default_output_path(
    *,
    repo_root: Path,
    format_id: str,
    rating_bucket: str,
    month_window_label: str,
) -> Path:
    return (
        repo_root
        / "backend"
        / "app"
        / "data"
        / "meta"
        / format_id
        / rating_bucket
        / f"{month_window_label}.json"
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build a normalized Espurr meta snapshot from a raw JSON payload."
    )
    parser.add_argument(
        "--input",
        required=True,
        help="Path to raw input JSON file.",
    )
    parser.add_argument(
        "--output",
        required=False,
        help="Optional explicit output path. If omitted, uses backend/app/data/meta/<format>/<rating>/rolling_3m.json",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    input_path = Path(args.input).resolve()
    raw_payload = json.loads(input_path.read_text(encoding="utf-8"))
    snapshot = build_snapshot(raw_payload)

    repo_root = Path(__file__).resolve().parents[2]

    if args.output:
        output_path = Path(args.output).resolve()
    else:
        output_path = default_output_path(
            repo_root=repo_root,
            format_id=str(snapshot["format_id"]),
            rating_bucket=str(snapshot["rating_bucket"]),
            month_window_label="rolling_3m",
        )

    _ensure_dir(output_path)
    output_path.write_text(json.dumps(snapshot, indent=2), encoding="utf-8")

    print(f"Wrote normalized snapshot to: {output_path}")


if __name__ == "__main__":
    main()