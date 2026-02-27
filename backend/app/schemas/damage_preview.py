from pydantic import BaseModel, Field
from typing import List, Literal, Optional

PokemonType = Literal[
    "Normal","Fire","Water","Electric","Grass","Ice",
    "Fighting","Poison","Ground","Flying","Psychic","Bug",
    "Rock","Ghost","Dragon","Dark","Steel","Fairy"
]

MoveCategory = Literal["physical", "special", "status"]

class MoveInfo(BaseModel):
    name: Optional[str] = None
    type: PokemonType
    power: Optional[int] = Field(default=None, ge=0)  # None/0 => status or variable
    category: MoveCategory

class CombatantInfo(BaseModel):
    types: List[PokemonType] = Field(min_length=1, max_length=2)
    atk: Optional[int] = Field(default=100, ge=1)   # fallback defaults
    def_: Optional[int] = Field(default=100, ge=1)  # defense (physical)
    spa: Optional[int] = Field(default=100, ge=1)   # special attack
    spd: Optional[int] = Field(default=100, ge=1)   # special defense
    hp: Optional[int] = Field(default=100, ge=1)    # used only to convert to %

class DamagePreviewRequest(BaseModel):
    attacker: CombatantInfo
    defender: CombatantInfo
    move: MoveInfo

class DamagePreviewResponse(BaseModel):
    moveType: PokemonType
    moveCategory: MoveCategory
    basePower: int
    stab: float
    typeMultiplier: float
    estimatedDamage: float
    estimatedDamagePercent: float
    notes: List[str]