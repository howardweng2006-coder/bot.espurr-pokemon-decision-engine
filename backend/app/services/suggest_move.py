from __future__ import annotations

from typing import List, Tuple

from app.schemas.damage_preview import CombatantInfo, MoveInfo
from app.services.battle_state_service import evaluate_manual_inputs


def suggest_move(
    attacker: CombatantInfo,
    defender: CombatantInfo,
    moves: List[MoveInfo],
    temperature: float = 8.0,
) -> Tuple[str, float, List[dict], str]:
    return evaluate_manual_inputs(
        attacker=attacker,
        defender=defender,
        moves=moves,
        temperature=temperature,
    )
