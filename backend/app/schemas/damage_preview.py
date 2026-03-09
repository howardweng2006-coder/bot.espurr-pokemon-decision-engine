from pydantic import BaseModel, Field
from typing import List, Literal, Optional

PokemonType = Literal[
    "Normal", "Fire", "Water", "Electric", "Grass", "Ice",
    "Fighting", "Poison", "Ground", "Flying", "Psychic", "Bug",
    "Rock", "Ghost", "Dragon", "Dark", "Steel", "Fairy"
]

MoveCategory = Literal["physical", "special", "status"]


class MoveInfo(BaseModel):
    name: Optional[str] = None
    type: PokemonType
    power: Optional[int] = Field(default=None, ge=0)
    category: MoveCategory
    crit: bool = False
    level: Optional[int] = Field(default=None, ge=1, le=100)


class CombatantInfo(BaseModel):
    types: List[PokemonType] = Field(min_length=1, max_length=2)
    atk: Optional[int] = Field(default=100, ge=1)
    def_: Optional[int] = Field(default=100, ge=1)
    spa: Optional[int] = Field(default=100, ge=1)
    spd: Optional[int] = Field(default=100, ge=1)
    hp: Optional[int] = Field(default=100, ge=1)
    level: Optional[int] = Field(default=None, ge=1, le=100)
    burned: bool = False
    tera_active: bool = False


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
    minDamage: float
    maxDamage: float
    minDamagePercent: float
    maxDamagePercent: float
    level: int
    critApplied: bool
    burnApplied: bool
    notes: List[str]