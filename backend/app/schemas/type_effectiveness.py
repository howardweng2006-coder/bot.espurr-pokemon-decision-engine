from pydantic import BaseModel, Field
from typing import List, Literal

# Optional: restrict to valid types (helps frontend correctness)
PokemonType = Literal[
    "Normal","Fire","Water","Electric","Grass","Ice",
    "Fighting","Poison","Ground","Flying","Psychic","Bug",
    "Rock","Ghost","Dragon","Dark","Steel","Fairy"
]

class TypeEffectivenessRequest(BaseModel):
    moveType: PokemonType
    defenderTypes: List[PokemonType] = Field(min_length=1, max_length=2)

class TypeEffectivenessResponse(BaseModel):
    moveType: PokemonType
    defenderTypes: List[PokemonType]
    multiplier: float
    breakdown: List[dict]