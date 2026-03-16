from typing import List, Literal, Optional

from pydantic import BaseModel, Field, ConfigDict

from app.schemas.damage_preview import CombatantInfo, MoveInfo
from app.schemas.suggest_move import ActionOption


StatusCondition = Literal["brn", "par", "psn", "tox", "slp", "frz"]
Weather = Literal["sun", "rain", "sand", "snow"]
Terrain = Literal["electric", "grassy", "misty", "psychic"]


class StatBoosts(BaseModel):
    atk: int = Field(default=0, ge=-6, le=6)
    def_: int = Field(default=0, ge=-6, le=6)
    spa: int = Field(default=0, ge=-6, le=6)
    spd: int = Field(default=0, ge=-6, le=6)
    spe: int = Field(default=0, ge=-6, le=6)


class ActivePokemonState(CombatantInfo):
    species: Optional[str] = None
    spe: Optional[int] = Field(default=100, ge=1)
    currentHp: Optional[int] = Field(default=None, ge=0)
    status: Optional[StatusCondition] = None
    boosts: StatBoosts = Field(default_factory=StatBoosts)


class SwitchCandidate(BaseModel):
    species: str
    types: List[str] = Field(min_length=1, max_length=2)
    atk: Optional[int] = Field(default=100, ge=1)
    def_: Optional[int] = Field(default=100, ge=1)
    spa: Optional[int] = Field(default=100, ge=1)
    spd: Optional[int] = Field(default=100, ge=1)
    spe: Optional[int] = Field(default=100, ge=1)
    hp: Optional[int] = Field(default=100, ge=1)
    currentHp: Optional[int] = Field(default=None, ge=0)
    burned: bool = False
    tera_active: bool = False
    status: Optional[StatusCondition] = None


class SideHazards(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    stealth_rock: bool = Field(default=False, alias="stealthRock")
    spikes_layers: int = Field(default=0, ge=0, le=3, alias="spikesLayers")
    sticky_web: bool = Field(default=False, alias="stickyWeb")
    toxic_spikes_layers: int = Field(default=0, ge=0, le=2, alias="toxicSpikesLayers")


class FieldState(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    weather: Optional[Weather] = None
    terrain: Optional[Terrain] = None
    attacker_side: SideHazards = Field(default_factory=SideHazards, alias="attackerSide")
    defender_side: SideHazards = Field(default_factory=SideHazards, alias="defenderSide")


class BattleStateRequest(BaseModel):
    attacker: ActivePokemonState
    defender: ActivePokemonState
    moves: List[MoveInfo] = Field(min_length=1, max_length=24)
    availableSwitches: List[SwitchCandidate] = Field(default_factory=list)
    field: FieldState = Field(default_factory=FieldState)
    generation: int = Field(default=9, ge=1, le=9)
    formatName: Optional[str] = "manual"


class EvaluatePositionResponse(BaseModel):
    bestAction: str
    confidence: float
    rankedActions: List[ActionOption]
    explanation: str
    assumptionsUsed: List[str]
