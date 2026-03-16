from pydantic import BaseModel, Field
from typing import List, Literal, Optional

from app.schemas.damage_preview import CombatantInfo, MoveInfo


class SuggestMoveRequest(BaseModel):
    attacker: CombatantInfo
    defender: CombatantInfo
    moves: List[MoveInfo] = Field(min_length=1, max_length=24)


class MoveOption(BaseModel):
    name: str
    moveType: str
    moveCategory: str
    basePower: int
    stab: float
    typeMultiplier: float
    minDamage: float
    maxDamage: float
    minDamagePercent: float
    maxDamagePercent: float
    score: float
    confidence: float
    notes: List[str]


class ActionOption(BaseModel):
    actionType: Literal["move", "switch"]
    name: str
    moveType: Optional[str] = None
    moveCategory: Optional[str] = None
    basePower: Optional[int] = None
    typeMultiplier: Optional[float] = None
    minDamage: Optional[float] = None
    maxDamage: Optional[float] = None
    minDamagePercent: Optional[float] = None
    maxDamagePercent: Optional[float] = None
    score: float
    confidence: float
    notes: List[str]


class SuggestMoveResponse(BaseModel):
    bestMove: str
    confidence: float
    rankedMoves: List[MoveOption]
    explanation: str
