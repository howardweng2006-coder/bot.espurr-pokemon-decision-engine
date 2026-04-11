from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from app.inference.models import (
    MetaPriorSnapshot,
    PairAssociations,
    SpeciesPrior,
    WeightedSpread,
    WeightedValue,
)
from app.providers.meta_loader import default_meta_base_dir, load_snapshot_from_disk


@dataclass(frozen=True)
class MetaQuery:
    format_id: str
    generation: int
    rating_bucket: str = "1695"
    month_window: int = 3


def _great_tusk_prior() -> SpeciesPrior:
    return SpeciesPrior(
        species="Great Tusk",
        usage_weight=1.0,
        moves=[
            WeightedValue("Headlong Rush", 0.95),
            WeightedValue("Earthquake", 0.82),
            WeightedValue("Knock Off", 0.80),
            WeightedValue("Rapid Spin", 0.78),
            WeightedValue("Stealth Rock", 0.68),
            WeightedValue("Close Combat", 0.52),
            WeightedValue("Ice Spinner", 0.47),
        ],
        items=[
            WeightedValue("Leftovers", 0.42),
            WeightedValue("Booster Energy", 0.33),
            WeightedValue("Choice Scarf", 0.12),
            WeightedValue("Heavy-Duty Boots", 0.08),
        ],
        abilities=[
            WeightedValue("Protosynthesis", 1.0),
        ],
        tera_types=[
            WeightedValue("Water", 0.24),
            WeightedValue("Steel", 0.20),
            WeightedValue("Ghost", 0.16),
            WeightedValue("Fire", 0.10),
            WeightedValue("Poison", 0.08),
        ],
        spreads=[
            WeightedSpread(
                label="bulky-utility",
                nature="Impish",
                evs={"hp": 252, "atk": 52, "def": 204},
                ivs={},
                weight=0.42,
            ),
            WeightedSpread(
                label="offensive-spinner",
                nature="Jolly",
                evs={"atk": 252, "def": 4, "spe": 252},
                ivs={},
                weight=0.35,
            ),
            WeightedSpread(
                label="scarf-attacker",
                nature="Jolly",
                evs={"atk": 252, "def": 4, "spe": 252},
                ivs={},
                weight=0.13,
            ),
        ],
        teammate_weights=[],
        lead_weights=[],
        associations=PairAssociations(),
        notes=[
            "Built-in V1 provider prior.",
            "Fallback only until disk-backed normalized snapshots are loaded.",
        ],
    )


def _kingambit_prior() -> SpeciesPrior:
    return SpeciesPrior(
        species="Kingambit",
        usage_weight=1.0,
        moves=[
            WeightedValue("Kowtow Cleave", 0.98),
            WeightedValue("Sucker Punch", 0.96),
            WeightedValue("Iron Head", 0.72),
            WeightedValue("Swords Dance", 0.66),
            WeightedValue("Low Kick", 0.38),
            WeightedValue("Tera Blast", 0.20),
        ],
        items=[
            WeightedValue("Black Glasses", 0.40),
            WeightedValue("Leftovers", 0.26),
            WeightedValue("Choice Band", 0.18),
            WeightedValue("Lum Berry", 0.06),
        ],
        abilities=[
            WeightedValue("Supreme Overlord", 1.0),
        ],
        tera_types=[
            WeightedValue("Dark", 0.34),
            WeightedValue("Flying", 0.20),
            WeightedValue("Fire", 0.12),
            WeightedValue("Fairy", 0.10),
            WeightedValue("Ghost", 0.08),
        ],
        spreads=[
            WeightedSpread(
                label="black-glasses-sd",
                nature="Adamant",
                evs={"hp": 112, "atk": 252, "spe": 144},
                ivs={},
                weight=0.40,
            ),
            WeightedSpread(
                label="leftovers-bulky",
                nature="Careful",
                evs={"hp": 252, "atk": 56, "spd": 200},
                ivs={},
                weight=0.28,
            ),
            WeightedSpread(
                label="banded-attacker",
                nature="Adamant",
                evs={"hp": 176, "atk": 252, "spe": 80},
                ivs={},
                weight=0.18,
            ),
        ],
        teammate_weights=[],
        lead_weights=[],
        associations=PairAssociations(),
        notes=[
            "Built-in V1 provider prior.",
            "Fallback only until disk-backed normalized snapshots are loaded.",
        ],
    )


class MetaProvider:
    def __init__(self, base_dir: Path | None = None) -> None:
        self._base_dir = base_dir or default_meta_base_dir()
        self._memory_snapshots: dict[tuple[str, int, str, int], MetaPriorSnapshot] = {}
        self._seed_builtin_snapshots()

    def _seed_builtin_snapshots(self) -> None:
        key = ("gen9ou", 9, "1695", 3)
        self._memory_snapshots[key] = MetaPriorSnapshot(
            format_id="gen9ou",
            generation=9,
            rating_bucket="1695",
            month_window=["rolling-3m-v1"],
            species_priors={
                "Great Tusk": _great_tusk_prior(),
                "Kingambit": _kingambit_prior(),
            },
            notes=[
                "Built-in in-memory Gen 9 OU priors.",
                "Used only when disk-backed snapshots are unavailable.",
            ],
        )

    def get_snapshot(self, query: MetaQuery) -> MetaPriorSnapshot:
        disk_snapshot = load_snapshot_from_disk(
            base_dir=self._base_dir,
            format_id=query.format_id,
            generation=query.generation,
            rating_bucket=query.rating_bucket,
            month_window=query.month_window,
        )
        if disk_snapshot is not None:
            return disk_snapshot

        key = (query.format_id, query.generation, query.rating_bucket, query.month_window)
        memory_snapshot = self._memory_snapshots.get(key)
        if memory_snapshot is not None:
            return memory_snapshot

        return MetaPriorSnapshot(
            format_id=query.format_id,
            generation=query.generation,
            rating_bucket=query.rating_bucket,
            month_window=[f"rolling-{query.month_window}m-unavailable"],
            species_priors={},
            notes=["No snapshot available for requested meta query."],
        )

    def get_species_prior(self, query: MetaQuery, species: str) -> Optional[SpeciesPrior]:
        snapshot = self.get_snapshot(query)
        return snapshot.species_priors.get(species)