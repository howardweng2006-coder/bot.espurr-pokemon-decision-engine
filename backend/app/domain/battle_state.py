from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class StatBoosts:
    atk: int = 0
    def_: int = 0
    spa: int = 0
    spd: int = 0
    spe: int = 0


@dataclass
class ActivePokemon:
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
    boosts: StatBoosts = field(default_factory=StatBoosts)


@dataclass
class SideHazards:
    stealth_rock: bool = False
    spikes_layers: int = 0
    sticky_web: bool = False
    toxic_spikes_layers: int = 0


@dataclass
class FieldState:
    weather: Optional[str] = None
    terrain: Optional[str] = None
    attacker_side: SideHazards = field(default_factory=SideHazards)
    defender_side: SideHazards = field(default_factory=SideHazards)


@dataclass
class BattleState:
    attacker: ActivePokemon
    defender: ActivePokemon
    moves: List[object]
    available_switches: List[ActivePokemon] = field(default_factory=list)
    field: FieldState = field(default_factory=FieldState)
    generation: int = 9
    format_name: str = "manual"
