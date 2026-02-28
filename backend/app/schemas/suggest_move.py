from pydantic import BaseModel, Field
from typing import List, Optional

from app.schemas.damage_preview import CombatantInfo, MoveInfo


class SuggestMoveRequest(BaseModel):
    attacker: CombatantInfo
    defender: CombatantInfo
    moves: List[MoveInfo] = Field(min_length=1, max_length=24)  # allow more than 4 for testing


class MoveOption(BaseModel):
    name: str
    moveType: str
    moveCategory: str
    basePower: int
    stab: float
    typeMultiplier: float
    estimatedDamage: float
    estimatedDamagePercent: float
    score: float
    confidence: float
    notes: List[str]


class SuggestMoveResponse(BaseModel):
    bestMove: str
    confidence: float
    rankedMoves: List[MoveOption]
    explanation: str