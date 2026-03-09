from pydantic import BaseModel
from typing import Dict, List

class SearchListResponse(BaseModel):
    results: List[str]

class PokemonDetailResponse(BaseModel):
    name: str
    types: List[str]
    base: Dict[str, int]

class MoveDetailResponse(BaseModel):
    name: str
    type: str
    category: str
    power: int