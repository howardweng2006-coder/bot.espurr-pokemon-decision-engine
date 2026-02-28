from pydantic import BaseModel
from typing import List, Dict, Any

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