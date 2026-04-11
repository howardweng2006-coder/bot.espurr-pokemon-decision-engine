from __future__ import annotations

from typing import Any

from app.inference.models import (
    MetaPriorSnapshot,
    PairAssociations,
    SpeciesPrior,
    WeightedPair,
    WeightedSpread,
    WeightedValue,
)


def _weighted_value_from_dict(payload: dict[str, Any]) -> WeightedValue:
    return WeightedValue(
        value=str(payload.get("value", "")),
        weight=float(payload.get("weight", 0.0)),
        source_weight=float(payload.get("source_weight", 1.0)),
        notes=list(payload.get("notes", [])),
    )


def _weighted_spread_from_dict(payload: dict[str, Any]) -> WeightedSpread:
    return WeightedSpread(
        label=str(payload.get("label", "unknown-spread")),
        nature=payload.get("nature"),
        evs=dict(payload.get("evs", {})),
        ivs=dict(payload.get("ivs", {})),
        weight=float(payload.get("weight", 0.0)),
        source_weight=float(payload.get("source_weight", 1.0)),
        notes=list(payload.get("notes", [])),
    )


def _weighted_pair_from_dict(payload: dict[str, Any]) -> WeightedPair:
    return WeightedPair(
        left=str(payload.get("left", "")),
        right=str(payload.get("right", "")),
        weight=float(payload.get("weight", 0.0)),
        notes=list(payload.get("notes", [])),
    )


def _pair_associations_from_dict(payload: dict[str, Any]) -> PairAssociations:
    return PairAssociations(
        move_move=[_weighted_pair_from_dict(x) for x in payload.get("move_move", [])],
        move_item=[_weighted_pair_from_dict(x) for x in payload.get("move_item", [])],
        move_ability=[_weighted_pair_from_dict(x) for x in payload.get("move_ability", [])],
        move_tera=[_weighted_pair_from_dict(x) for x in payload.get("move_tera", [])],
        item_ability=[_weighted_pair_from_dict(x) for x in payload.get("item_ability", [])],
        item_spread=[_weighted_pair_from_dict(x) for x in payload.get("item_spread", [])],
        ability_tera=[_weighted_pair_from_dict(x) for x in payload.get("ability_tera", [])],
    )


def species_prior_from_dict(payload: dict[str, Any]) -> SpeciesPrior:
    return SpeciesPrior(
        species=str(payload.get("species", "")),
        usage_weight=float(payload.get("usage_weight", 0.0)),
        moves=[_weighted_value_from_dict(x) for x in payload.get("moves", [])],
        items=[_weighted_value_from_dict(x) for x in payload.get("items", [])],
        abilities=[_weighted_value_from_dict(x) for x in payload.get("abilities", [])],
        tera_types=[_weighted_value_from_dict(x) for x in payload.get("tera_types", [])],
        spreads=[_weighted_spread_from_dict(x) for x in payload.get("spreads", [])],
        teammate_weights=[_weighted_value_from_dict(x) for x in payload.get("teammate_weights", [])],
        lead_weights=[_weighted_value_from_dict(x) for x in payload.get("lead_weights", [])],
        associations=_pair_associations_from_dict(payload.get("associations", {})),
        notes=list(payload.get("notes", [])),
    )


def snapshot_from_dict(payload: dict[str, Any]) -> MetaPriorSnapshot:
    raw_species = dict(payload.get("species_priors", {}))
    species_priors = {
        species_name: species_prior_from_dict(species_payload)
        for species_name, species_payload in raw_species.items()
    }

    return MetaPriorSnapshot(
        format_id=str(payload.get("format_id", "")),
        generation=int(payload.get("generation", 0)),
        rating_bucket=str(payload.get("rating_bucket", "")),
        month_window=list(payload.get("month_window", [])),
        species_priors=species_priors,
        notes=list(payload.get("notes", [])),
    )