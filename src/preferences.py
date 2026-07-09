"""Coach preferences that guide lineup optimization."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple

from models import Position


@dataclass(frozen=True)
class PositionAvoidance:
    player_name: str
    position: Position
    innings: Tuple[int, ...] = ()

    def applies_to(self, player_name: str, position: Position, inning: int) -> bool:
        return (
            self.player_name == player_name
            and self.position is position
            and (not self.innings or inning in self.innings)
        )


@dataclass(frozen=True)
class CoachPreferences:
    top_defenders: Tuple[str, ...] = ()
    development_focus: Tuple[str, ...] = ()
    avoid_positions: Tuple[PositionAvoidance, ...] = ()
    spread_first_inning_infield_strength: bool = True
