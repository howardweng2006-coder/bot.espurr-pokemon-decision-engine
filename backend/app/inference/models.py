from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class CandidateSet:
    species: Optional[str]
    label: str
    moves: List[str] = field(default_factory=list)
    item: Optional[str] = None
    ability: Optional[str] = None
    tera_type: Optional[str] = None
    weight: float = 1.0
    source: str = "placeholder"


@dataclass
class InferenceResult:
    species: Optional[str]
    candidates: List[CandidateSet] = field(default_factory=list)
    confidence_label: str = "unknown"
    notes: List[str] = field(default_factory=list)

    def normalized_weights(self) -> Dict[str, float]:
        total = sum(candidate.weight for candidate in self.candidates) or 1.0
        return {
            candidate.label: candidate.weight / total
            for candidate in self.candidates
        }