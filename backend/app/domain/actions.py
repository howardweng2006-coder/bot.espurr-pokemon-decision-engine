from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Optional


ActionType = Literal["move", "switch"]


@dataclass
class MoveAction:
    action_type: ActionType
    move_name: str


@dataclass
class SwitchAction:
    action_type: ActionType
    target_species: str
