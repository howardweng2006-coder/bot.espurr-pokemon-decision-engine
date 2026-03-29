from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal, Optional, Union


ActionType = Literal["move", "switch"]


@dataclass(frozen=True)
class MoveAction:
    move_name: str
    move_type: str
    move_category: str
    base_power: int
    priority: int = 0
    action_type: ActionType = "move"


@dataclass(frozen=True)
class SwitchAction:
    target_species: str
    action_type: ActionType = "switch"


Action = Union[MoveAction, SwitchAction]


@dataclass
class EvaluatedAction:
    action: Action
    score: float
    confidence: float = 0.0
    notes: list[str] = field(default_factory=list)

    type_multiplier: Optional[float] = None
    min_damage: Optional[float] = None
    max_damage: Optional[float] = None
    min_damage_percent: Optional[float] = None
    max_damage_percent: Optional[float] = None

    @property
    def action_type(self) -> ActionType:
        return self.action.action_type

    @property
    def name(self) -> str:
        if isinstance(self.action, MoveAction):
            return self.action.move_name
        return self.action.target_species

    def to_dict(self) -> dict:
        if isinstance(self.action, MoveAction):
            return {
                "actionType": self.action.action_type,
                "name": self.action.move_name,
                "moveType": self.action.move_type,
                "moveCategory": self.action.move_category,
                "basePower": self.action.base_power,
                "typeMultiplier": self.type_multiplier,
                "minDamage": self.min_damage,
                "maxDamage": self.max_damage,
                "minDamagePercent": self.min_damage_percent,
                "maxDamagePercent": self.max_damage_percent,
                "score": self.score,
                "confidence": self.confidence,
                "notes": self.notes,
            }

        return {
            "actionType": self.action.action_type,
            "name": self.action.target_species,
            "moveType": None,
            "moveCategory": None,
            "basePower": None,
            "typeMultiplier": None,
            "minDamage": None,
            "maxDamage": None,
            "minDamagePercent": None,
            "maxDamagePercent": None,
            "score": self.score,
            "confidence": self.confidence,
            "notes": self.notes,
        }