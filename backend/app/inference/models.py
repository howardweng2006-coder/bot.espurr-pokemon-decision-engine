from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Literal, Optional


ResponseKind = Literal["move", "switch"]
EvidenceDecision = Literal["keep", "downweight", "eliminate"]
ConstraintKind = Literal["confirmed", "constrained", "meta_inferred"]


@dataclass(frozen=True)
class WeightedValue:
    value: str
    weight: float
    source_weight: float = 1.0
    notes: List[str] = field(default_factory=list)


@dataclass(frozen=True)
class WeightedSpread:
    label: str
    nature: Optional[str] = None
    evs: Dict[str, int] = field(default_factory=dict)
    ivs: Dict[str, int] = field(default_factory=dict)
    weight: float = 0.0
    source_weight: float = 1.0
    notes: List[str] = field(default_factory=list)


@dataclass(frozen=True)
class WeightedPair:
    left: str
    right: str
    weight: float
    notes: List[str] = field(default_factory=list)


@dataclass(frozen=True)
class PairAssociations:
    move_move: List[WeightedPair] = field(default_factory=list)
    move_item: List[WeightedPair] = field(default_factory=list)
    move_ability: List[WeightedPair] = field(default_factory=list)
    move_tera: List[WeightedPair] = field(default_factory=list)
    item_ability: List[WeightedPair] = field(default_factory=list)
    item_spread: List[WeightedPair] = field(default_factory=list)
    ability_tera: List[WeightedPair] = field(default_factory=list)


@dataclass(frozen=True)
class SpeciesPrior:
    species: str
    usage_weight: float

    moves: List[WeightedValue] = field(default_factory=list)
    items: List[WeightedValue] = field(default_factory=list)
    abilities: List[WeightedValue] = field(default_factory=list)
    tera_types: List[WeightedValue] = field(default_factory=list)
    spreads: List[WeightedSpread] = field(default_factory=list)

    teammate_weights: List[WeightedValue] = field(default_factory=list)
    lead_weights: List[WeightedValue] = field(default_factory=list)

    associations: PairAssociations = field(default_factory=PairAssociations)
    notes: List[str] = field(default_factory=list)


@dataclass(frozen=True)
class MetaPriorSnapshot:
    format_id: str
    generation: int
    rating_bucket: str
    month_window: List[str]
    species_priors: Dict[str, SpeciesPrior] = field(default_factory=dict)
    notes: List[str] = field(default_factory=list)


@dataclass
class CandidateConstraint:
    kind: ConstraintKind
    field_name: str
    expected_value: str
    source: str
    hard: bool = False
    notes: List[str] = field(default_factory=list)


@dataclass
class CandidateCheckResult:
    decision: EvidenceDecision
    multiplier: float = 1.0
    reasons: List[str] = field(default_factory=list)


@dataclass
class CandidateBuilderConfig:
    max_moves_per_set: int = 4
    max_candidates: int = 12

    top_moves: int = 12
    top_items: int = 6
    top_abilities: int = 4
    top_tera_types: int = 6
    top_spreads: int = 6

    min_weight_threshold: float = 0.01
    pair_weight_floor: float = 0.05

    preserve_revealed_moves: bool = True
    soft_downweight_unusual: bool = True
    hard_eliminate_contradictions: bool = True


@dataclass
class CandidateSet:
    species: str
    label: str

    moves: List[str] = field(default_factory=list)
    item: Optional[str] = None
    ability: Optional[str] = None
    tera_type: Optional[str] = None
    spread_label: Optional[str] = None
    nature: Optional[str] = None
    evs: Dict[str, int] = field(default_factory=dict)
    ivs: Dict[str, int] = field(default_factory=dict)

    prior_weight: float = 0.0
    compatibility_weight: float = 1.0
    evidence_weight: float = 1.0
    final_weight: float = 0.0

    source: str = "meta_provider"

    confirmed_moves: List[str] = field(default_factory=list)
    assumed_moves: List[str] = field(default_factory=list)

    notes: List[str] = field(default_factory=list)
    penalties: List[str] = field(default_factory=list)
    elimination_reasons: List[str] = field(default_factory=list)

    @property
    def is_eliminated(self) -> bool:
        return bool(self.elimination_reasons)


@dataclass
class InferenceResult:
    species: Optional[str]
    candidates: List[CandidateSet] = field(default_factory=list)
    confidence_label: str = "unknown"
    notes: List[str] = field(default_factory=list)

    def normalized_weights(self) -> Dict[str, float]:
        viable = [candidate for candidate in self.candidates if not candidate.is_eliminated]
        total = sum(candidate.final_weight for candidate in viable) or 1.0
        return {
            candidate.label: candidate.final_weight / total
            for candidate in viable
        }


@dataclass
class OpponentWorld:
    species: Optional[str]
    candidate: CandidateSet
    weight: float

    known_moves: List[str] = field(default_factory=list)
    assumed_moves: List[str] = field(default_factory=list)

    assumed_item: Optional[str] = None
    assumed_ability: Optional[str] = None
    assumed_tera_type: Optional[str] = None
    assumed_spread_label: Optional[str] = None

    notes: List[str] = field(default_factory=list)


@dataclass
class OpponentResponse:
    kind: ResponseKind
    label: str
    weight: float

    move_name: Optional[str] = None
    move_type: Optional[str] = None
    move_category: Optional[str] = None
    base_power: int = 0
    priority: int = 0

    switch_target_species: Optional[str] = None

    notes: List[str] = field(default_factory=list)


@dataclass
class ProjectionSummary:
    my_hp_before: float
    my_hp_after: float
    opp_hp_before: float
    opp_hp_after: float
    my_fainted: bool
    opp_fainted: bool
    order_context: str
    notes: List[str] = field(default_factory=list)

    my_active_species_after: Optional[str] = None
    opp_active_species_after: Optional[str] = None

    my_forced_switch: bool = False
    opp_forced_switch: bool = False
    opponent_switched: bool = False

    revealed_response_move: Optional[str] = None

    @property
    def my_damage_taken(self) -> float:
        return max(0.0, self.my_hp_before - self.my_hp_after)

    @property
    def opp_damage_taken(self) -> float:
        return max(0.0, self.opp_hp_before - self.opp_hp_after)

    @property
    def my_damage_taken_pct_current(self) -> float:
        if self.my_hp_before <= 0:
            return 0.0
        return min(100.0, (self.my_damage_taken / self.my_hp_before) * 100.0)

    @property
    def opp_damage_taken_pct_current(self) -> float:
        if self.opp_hp_before <= 0:
            return 0.0
        return min(100.0, (self.opp_damage_taken / self.opp_hp_before) * 100.0)


@dataclass
class ActionWorldEvaluation:
    world: OpponentWorld
    expected_score: float
    worst_score: float
    best_score: float
    response_breakdown: List[dict] = field(default_factory=list)
    notes: List[str] = field(default_factory=list)


@dataclass
class AggregatedActionValue:
    expected_score: float
    worst_score: float
    best_score: float
    stability: float = 0.0
    notes: List[str] = field(default_factory=list)