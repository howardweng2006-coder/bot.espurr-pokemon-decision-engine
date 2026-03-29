from __future__ import annotations

from dataclasses import dataclass, field as dc_field
from typing import Any, List, Optional


@dataclass
class StatBoosts:
    atk: int = 0
    def_: int = 0
    spa: int = 0
    spd: int = 0
    spe: int = 0


@dataclass
class PokemonState:
    species: Optional[str]
    types: List[str]
    atk: float = 100
    def_: float = 100
    spa: float = 100
    spd: float = 100
    spe: float = 100
    hp: float = 100
    level: Optional[int] = None
    burned: bool = False
    tera_active: bool = False
    current_hp: Optional[float] = None
    status: Optional[str] = None
    boosts: StatBoosts = dc_field(default_factory=StatBoosts)
    revealed_moves: List[str] = dc_field(default_factory=list)


@dataclass
class SideConditions:
    stealth_rock: bool = False
    spikes_layers: int = 0
    sticky_web: bool = False
    toxic_spikes_layers: int = 0


@dataclass
class SideState:
    active: PokemonState
    bench: List[PokemonState] = dc_field(default_factory=list)
    side_conditions: SideConditions = dc_field(default_factory=SideConditions)


@dataclass
class FieldState:
    weather: Optional[str] = None
    terrain: Optional[str] = None


@dataclass
class FormatContext:
    generation: int = 9
    format_name: str = "manual"
    ruleset: List[str] = dc_field(default_factory=list)


@dataclass
class BattleState:
    my_side: SideState
    opponent_side: SideState
    moves: List[Any] = dc_field(default_factory=list)
    field: FieldState = dc_field(default_factory=FieldState)
    format_context: FormatContext = dc_field(default_factory=FormatContext)

    @property
    def attacker_side_conditions(self) -> SideConditions:
        return self.my_side.side_conditions

    @property
    def defender_side_conditions(self) -> SideConditions:
        return self.opponent_side.side_conditions

