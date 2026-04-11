from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


SEPARATOR_RE = re.compile(r"^\+-+\+$")
BOX_LINE_RE = re.compile(r"^\|\s*(?P<content>.*?)\s*\|$")
TRAILING_PERCENT_RE = re.compile(r"^(?P<name>.+?)\s+(?P<value>[\d.]+)%$")

SECTION_NAMES = {
    "abilities",
    "items",
    "spreads",
    "moves",
    "tera types",
    "teammates",
    "checks and counters",
}

METADATA_PREFIXES = (
    "Raw count:",
    "Avg. weight:",
    "Viability Ceiling:",
)

SUPPORTED_SECTIONS = {
    "abilities",
    "items",
    "spreads",
    "moves",
    "tera types",
    "teammates",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Parse Smogon moveset stats into an Espurr raw meta payload."
    )
    parser.add_argument(
    "--moveset",
    required=True,
    nargs="+",
    help="One or more Smogon moveset txt files.",
    )
    parser.add_argument("--format-id", default="gen9ou")
    parser.add_argument("--generation", type=int, default=9)
    parser.add_argument("--rating-bucket", default="1695")
    parser.add_argument("--output", required=True, help="Path to raw output JSON file.")
    parser.add_argument("--top-species", type=int, default=30)
    parser.add_argument("--top-moves", type=int, default=8)
    parser.add_argument("--top-items", type=int, default=6)
    parser.add_argument("--top-abilities", type=int, default=3)
    parser.add_argument("--top-spreads", type=int, default=6)
    parser.add_argument("--top-teammates", type=int, default=10)
    parser.add_argument("--include-tera-types", action="store_true")
    return parser.parse_args()


def _normalize_percent(value: float) -> float:
    return max(0.0, min(1.0, value / 100.0))


def _clean_name(value: str) -> str:
    return " ".join(value.strip().split())


def _empty_species_payload() -> dict[str, Any]:
    return {
        "usage_weight": 1.0,
        "moves": [],
        "items": [],
        "abilities": [],
        "tera_types": [],
        "spreads": [],
        "teammate_weights": [],
        "lead_weights": [],
        "associations": {},
        "notes": ["Generated from Smogon moveset stats."],
    }


def _parse_spread_label(raw: str) -> tuple[str | None, dict[str, int]]:
    raw = raw.strip()
    if ":" not in raw:
        return None, {}

    nature, stat_blob = raw.split(":", 1)
    parts = [part.strip() for part in stat_blob.split("/")]
    if len(parts) != 6:
        return nature.strip(), {}

    stat_names = ["hp", "atk", "def", "spa", "spd", "spe"]
    evs: dict[str, int] = {}

    for stat_name, part in zip(stat_names, parts):
        try:
            value = int(part)
        except ValueError:
            value = 0
        if value:
            evs[stat_name] = value

    return nature.strip(), evs


def _parse_percent_row(content: str) -> tuple[str, float] | None:
    match = TRAILING_PERCENT_RE.match(content)
    if not match:
        return None

    name = _clean_name(match.group("name"))
    value = float(match.group("value"))
    return name, _normalize_percent(value)

def _rank_decay(rank_index: int) -> float:
    decay_table = [1.0, 0.9, 0.8, 0.7, 0.6, 0.5]
    if rank_index < len(decay_table):
        return decay_table[rank_index]
    return 0.4


def _pair_weight(left_weight: float, right_weight: float, *, decay: float = 1.0) -> float:
    return max(0.0, left_weight * right_weight * decay)


def _build_move_move_associations(
    moves: list[dict[str, Any]],
    *,
    max_moves: int = 6,
) -> list[dict[str, Any]]:
    selected = moves[:max_moves]
    pairs: list[dict[str, Any]] = []

    for i in range(len(selected)):
        for j in range(i + 1, len(selected)):
            left = selected[i]
            right = selected[j]
            rank_gap = j - i
            decay = max(0.4, 1.0 - (0.1 * rank_gap))
            pairs.append(
                {
                    "left": left["value"],
                    "right": right["value"],
                    "weight": _pair_weight(
                        float(left["weight"]),
                        float(right["weight"]),
                        decay=decay,
                    ),
                }
            )

    pairs.sort(key=lambda item: item["weight"], reverse=True)
    return pairs


def _build_move_item_associations(
    moves: list[dict[str, Any]],
    items: list[dict[str, Any]],
    *,
    max_moves: int = 6,
    max_items: int = 4,
) -> list[dict[str, Any]]:
    selected_moves = moves[:max_moves]
    selected_items = items[:max_items]
    pairs: list[dict[str, Any]] = []

    for item_index, item in enumerate(selected_items):
        item_decay = _rank_decay(item_index)
        for move_index, move in enumerate(selected_moves):
            move_decay = _rank_decay(move_index)
            decay = min(item_decay, move_decay)
            pairs.append(
                {
                    "left": move["value"],
                    "right": item["value"],
                    "weight": _pair_weight(
                        float(move["weight"]),
                        float(item["weight"]),
                        decay=decay,
                    ),
                }
            )

    pairs.sort(key=lambda item: item["weight"], reverse=True)
    return pairs


def _build_move_ability_associations(
    moves: list[dict[str, Any]],
    abilities: list[dict[str, Any]],
    *,
    max_moves: int = 6,
    max_abilities: int = 3,
) -> list[dict[str, Any]]:
    selected_moves = moves[:max_moves]
    selected_abilities = abilities[:max_abilities]
    pairs: list[dict[str, Any]] = []

    for ability_index, ability in enumerate(selected_abilities):
        ability_decay = _rank_decay(ability_index)
        for move_index, move in enumerate(selected_moves):
            move_decay = _rank_decay(move_index)
            decay = min(ability_decay, move_decay)
            pairs.append(
                {
                    "left": move["value"],
                    "right": ability["value"],
                    "weight": _pair_weight(
                        float(move["weight"]),
                        float(ability["weight"]),
                        decay=decay,
                    ),
                }
            )

    pairs.sort(key=lambda item: item["weight"], reverse=True)
    return pairs


def _build_item_spread_associations(
    items: list[dict[str, Any]],
    spreads: list[dict[str, Any]],
    *,
    max_items: int = 4,
    max_spreads: int = 4,
) -> list[dict[str, Any]]:
    selected_items = items[:max_items]
    selected_spreads = spreads[:max_spreads]
    pairs: list[dict[str, Any]] = []

    for item_index, item in enumerate(selected_items):
        item_decay = _rank_decay(item_index)
        for spread_index, spread in enumerate(selected_spreads):
            spread_decay = _rank_decay(spread_index)
            decay = min(item_decay, spread_decay)
            pairs.append(
                {
                    "left": item["value"],
                    "right": spread["label"],
                    "weight": _pair_weight(
                        float(item["weight"]),
                        float(spread["weight"]),
                        decay=decay,
                    ),
                }
            )

    pairs.sort(key=lambda item: item["weight"], reverse=True)
    return pairs


def _build_species_associations(payload: dict[str, Any]) -> dict[str, Any]:
    moves = list(payload.get("moves", []))
    items = list(payload.get("items", []))
    abilities = list(payload.get("abilities", []))
    spreads = list(payload.get("spreads", []))

    return {
        "move_move": _build_move_move_associations(moves),
        "move_item": _build_move_item_associations(moves, items),
        "move_ability": _build_move_ability_associations(moves, abilities),
        "move_tera": [],
        "item_ability": [],
        "item_spread": _build_item_spread_associations(items, spreads),
        "ability_tera": [],
    }

def parse_moveset_file(
    text: str,
    *,
    top_species: int,
    top_moves: int,
    top_items: int,
    top_abilities: int,
    top_spreads: int,
    top_teammates: int,
    include_tera_types: bool,
) -> dict[str, Any]:
    species_priors: dict[str, Any] = {}

    current_species: str | None = None
    current_section: str | None = None
    species_count = 0
    previous_was_separator = False

    for raw_line in text.splitlines():
        line = raw_line.rstrip()

        if SEPARATOR_RE.match(line):
            previous_was_separator = True
            continue

        box_match = BOX_LINE_RE.match(line)
        if not box_match:
            previous_was_separator = False
            continue

        content = _clean_name(box_match.group("content"))
        if not content:
            previous_was_separator = False
            continue

        lower_content = content.lower()

        # Metadata lines should never become species headers.
        if content.startswith(METADATA_PREFIXES):
            previous_was_separator = False
            continue

        # Section headers appear after separators.
        if previous_was_separator and lower_content in SECTION_NAMES:
            current_section = lower_content
            previous_was_separator = False
            continue

        # Species headers appear after separators, but only if the line is not:
        # - a section header
        # - a metadata line
        # - a percent row
        if previous_was_separator:
            if _parse_percent_row(content) is None:
                if species_count >= top_species:
                    break

                current_species = content
                current_section = None

                if current_species not in species_priors:
                    species_priors[current_species] = _empty_species_payload()
                    species_count += 1

                previous_was_separator = False
                continue

        previous_was_separator = False

        if current_species is None:
            continue

        if current_section not in SUPPORTED_SECTIONS:
            continue

        parsed = _parse_percent_row(content)
        if parsed is None:
            continue

        name, weight = parsed
        if name.lower() == "other":
            continue

        payload = species_priors[current_species]

        if current_section == "moves":
            if len(payload["moves"]) < top_moves:
                payload["moves"].append({"value": name, "weight": weight})

        elif current_section == "items":
            if len(payload["items"]) < top_items:
                payload["items"].append({"value": name, "weight": weight})

        elif current_section == "abilities":
            if len(payload["abilities"]) < top_abilities:
                payload["abilities"].append({"value": name, "weight": weight})

        elif current_section == "spreads":
            if len(payload["spreads"]) < top_spreads:
                nature, evs = _parse_spread_label(name)
                payload["spreads"].append(
                    {
                        "label": name,
                        "nature": nature,
                        "evs": evs,
                        "ivs": {},
                        "weight": weight,
                    }
                )

        elif current_section == "teammates":
            if len(payload["teammate_weights"]) < top_teammates:
                payload["teammate_weights"].append({"value": name, "weight": weight})

        elif current_section == "tera types" and include_tera_types:
            payload["tera_types"].append({"value": name, "weight": weight})
    
    for species_payload in species_priors.values():
        species_payload["associations"] = _build_species_associations(species_payload)

    return species_priors

def _merge_weighted_lists(
    monthly_lists: list[list[dict[str, Any]]],
    *,
    top_n: int,
) -> list[dict[str, Any]]:
    totals: dict[str, float] = {}

    for entries in monthly_lists:
        for entry in entries:
            name = str(entry["value"])
            weight = float(entry["weight"])
            totals[name] = totals.get(name, 0.0) + weight

    month_count = max(1, len(monthly_lists))
    averaged = [
        {"value": name, "weight": total / month_count}
        for name, total in totals.items()
    ]
    averaged.sort(key=lambda item: item["weight"], reverse=True)
    return averaged[:top_n]


def _merge_spreads(
    monthly_spreads: list[list[dict[str, Any]]],
    *,
    top_n: int,
) -> list[dict[str, Any]]:
    totals: dict[str, dict[str, Any]] = {}

    for spreads in monthly_spreads:
        for spread in spreads:
            label = str(spread["label"])
            existing = totals.get(label)
            if existing is None:
                totals[label] = {
                    "label": label,
                    "nature": spread.get("nature"),
                    "evs": dict(spread.get("evs", {})),
                    "ivs": dict(spread.get("ivs", {})),
                    "weight": float(spread.get("weight", 0.0)),
                }
            else:
                existing["weight"] += float(spread.get("weight", 0.0))

    month_count = max(1, len(monthly_spreads))
    merged = []
    for spread in totals.values():
        merged.append(
            {
                "label": spread["label"],
                "nature": spread.get("nature"),
                "evs": dict(spread.get("evs", {})),
                "ivs": dict(spread.get("ivs", {})),
                "weight": float(spread["weight"]) / month_count,
            }
        )

    merged.sort(key=lambda item: item["weight"], reverse=True)
    return merged[:top_n]

def _merge_weighted_pairs(
    monthly_lists: list[list[dict[str, Any]]],
    *,
    top_n: int,
) -> list[dict[str, Any]]:
    totals: dict[tuple[str, str], float] = {}

    for entries in monthly_lists:
        for entry in entries:
            key = (str(entry["left"]), str(entry["right"]))
            weight = float(entry["weight"])
            totals[key] = totals.get(key, 0.0) + weight

    month_count = max(1, len(monthly_lists))
    merged = [
        {"left": left, "right": right, "weight": total / month_count}
        for (left, right), total in totals.items()
    ]
    merged.sort(key=lambda item: item["weight"], reverse=True)
    return merged[:top_n]


def _merge_associations(monthly_payloads: list[dict[str, Any]]) -> dict[str, Any]:
    association_payloads = [payload.get("associations", {}) for payload in monthly_payloads]

    return {
        "move_move": _merge_weighted_pairs(
            [assoc.get("move_move", []) for assoc in association_payloads],
            top_n=20,
        ),
        "move_item": _merge_weighted_pairs(
            [assoc.get("move_item", []) for assoc in association_payloads],
            top_n=24,
        ),
        "move_ability": _merge_weighted_pairs(
            [assoc.get("move_ability", []) for assoc in association_payloads],
            top_n=18,
        ),
        "move_tera": [],
        "item_ability": [],
        "item_spread": _merge_weighted_pairs(
            [assoc.get("item_spread", []) for assoc in association_payloads],
            top_n=16,
        ),
        "ability_tera": [],
    }

def merge_species_priors(
    monthly_species_priors: list[dict[str, Any]],
    *,
    top_moves: int,
    top_items: int,
    top_abilities: int,
    top_spreads: int,
    top_teammates: int,
    include_tera_types: bool,
) -> dict[str, Any]:
    all_species: set[str] = set()
    for monthly in monthly_species_priors:
        all_species.update(monthly.keys())

    merged: dict[str, Any] = {}

    for species_name in sorted(all_species):
        monthly_payloads = [
            monthly[species_name]
            for monthly in monthly_species_priors
            if species_name in monthly
        ]

        merged_payload = _empty_species_payload()

        merged_payload["moves"] = _merge_weighted_lists(
            [payload.get("moves", []) for payload in monthly_payloads],
            top_n=top_moves,
        )
        merged_payload["items"] = _merge_weighted_lists(
            [payload.get("items", []) for payload in monthly_payloads],
            top_n=top_items,
        )
        merged_payload["abilities"] = _merge_weighted_lists(
            [payload.get("abilities", []) for payload in monthly_payloads],
            top_n=top_abilities,
        )
        merged_payload["spreads"] = _merge_spreads(
            [payload.get("spreads", []) for payload in monthly_payloads],
            top_n=top_spreads,
        )
        merged_payload["teammate_weights"] = _merge_weighted_lists(
            [payload.get("teammate_weights", []) for payload in monthly_payloads],
            top_n=top_teammates,
        )

        if include_tera_types:
            merged_payload["tera_types"] = _merge_weighted_lists(
                [payload.get("tera_types", []) for payload in monthly_payloads],
                top_n=10,
            )

        merged_payload["associations"] = _merge_associations(monthly_payloads)

        merged_payload["notes"] = [
            f"Merged from {len(monthly_payloads)} monthly Smogon moveset payload(s)."
        ]

        merged[species_name] = merged_payload

    return merged

def build_raw_payload(
    *,
    format_id: str,
    generation: int,
    rating_bucket: str,
    species_priors: dict[str, Any],
    source_label: str,
    include_tera_types: bool,
) -> dict[str, Any]:
    tera_note = (
        "Tera types included from parsed moveset source."
        if include_tera_types
        else "Tera types intentionally omitted from this ingestion pass."
    )

    return {
        "format_id": format_id,
        "generation": generation,
        "rating_bucket": rating_bucket,
        "month_window": [source_label],
        "species_priors": species_priors,
        "notes": [
            "Raw payload generated from Smogon moveset stats.",
            tera_note,
            "Associations/leads/checks-and-counters not yet ingested in this pass.",
        ],
    }


def main() -> None:
    args = parse_args()

    monthly_species_priors: list[dict[str, Any]] = []
    source_labels: list[str] = []

    for moveset_arg in args.moveset:
        moveset_path = Path(moveset_arg).resolve()
        text = moveset_path.read_text(encoding="utf-8", errors="replace")

        source_labels.append(moveset_path.stem)

        species_priors = parse_moveset_file(
            text,
            top_species=args.top_species,
            top_moves=args.top_moves,
            top_items=args.top_items,
            top_abilities=args.top_abilities,
            top_spreads=args.top_spreads,
            top_teammates=args.top_teammates,
            include_tera_types=args.include_tera_types,
        )
        monthly_species_priors.append(species_priors)

    if len(monthly_species_priors) == 1:
        merged_species_priors = monthly_species_priors[0]
        month_window = source_labels
    else:
        merged_species_priors = merge_species_priors(
            monthly_species_priors,
            top_moves=args.top_moves,
            top_items=args.top_items,
            top_abilities=args.top_abilities,
            top_spreads=args.top_spreads,
            top_teammates=args.top_teammates,
            include_tera_types=args.include_tera_types,
        )
        month_window = source_labels

    tera_note = (
        "Tera types included from parsed moveset source."
        if args.include_tera_types
        else "Tera types intentionally omitted from this ingestion pass."
    )

    payload = {
        "format_id": args.format_id,
        "generation": args.generation,
        "rating_bucket": args.rating_bucket,
        "month_window": month_window,
        "species_priors": merged_species_priors,
        "notes": [
            "Raw payload generated from Smogon moveset stats.",
            tera_note,
            "Associations/leads/checks-and-counters not yet ingested in this pass.",
        ],
    }

    output_path = Path(args.output).resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    print(f"Wrote raw Smogon-derived payload to: {output_path}")
    print(f"Merged month count: {len(monthly_species_priors)}")
    print(f"Parsed species count: {len(merged_species_priors)}")
    if merged_species_priors:
        preview = list(merged_species_priors.keys())[:5]
        print(f"Top parsed species preview: {preview}")


if __name__ == "__main__":
    main()