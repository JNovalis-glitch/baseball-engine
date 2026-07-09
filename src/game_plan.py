"""Load game plans from simple JSON data."""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

from models import Player, Position, Tier
from preferences import CoachPreferences, PositionAvoidance
from validator import PositionLock


@dataclass(frozen=True)
class GamePlan:
    players: tuple[Player, ...]
    locks: tuple[PositionLock, ...]
    preferences: CoachPreferences = CoachPreferences()


def load_game_plan(path: str | Path) -> GamePlan:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return parse_game_plan(data)


def parse_game_plan(data: dict[str, Any]) -> GamePlan:
    players = tuple(_parse_player(item) for item in data.get("players", []))
    locks = tuple(_parse_lock(item) for item in data.get("locks", []))
    preferences = _parse_preferences(data.get("preferences", {}))
    if not players:
        raise ValueError("Game plan must include players.")
    return GamePlan(players, locks, preferences)


def _parse_player(data: dict[str, Any]) -> Player:
    return Player(
        name=str(data["name"]),
        tier=Tier(str(data.get("tier", "B")).upper()),
        pitcher=bool(data.get("pitcher", False)),
        catcher=bool(data.get("catcher", False)),
        coach_kid=bool(data.get("coach_kid", False)),
        new_player=bool(data.get("new_player", False)),
        active=bool(data.get("active", True)),
    )


def _parse_lock(data: dict[str, Any]) -> PositionLock:
    return PositionLock(
        inning=int(data["inning"]),
        position=Position(str(data["position"]).upper()),
        player_name=str(_first_present(data, ("player", "player_name", "name"))),
    )


def _parse_preferences(data: dict[str, Any]) -> CoachPreferences:
    return CoachPreferences(
        top_defenders=tuple(data.get("top_defenders", ())),
        development_focus=tuple(data.get("development_focus", ())),
        avoid_positions=tuple(
            _parse_avoidance(item) for item in data.get("avoid_positions", ())
        ),
        spread_first_inning_infield_strength=bool(
            data.get("spread_first_inning_infield_strength", True)
        ),
    )


def _parse_avoidance(data: dict[str, Any]) -> PositionAvoidance:
    raw_innings = data.get("innings", ())
    if isinstance(raw_innings, int):
        innings = (raw_innings,)
    else:
        innings = tuple(int(inning) for inning in raw_innings)
    return PositionAvoidance(
        player_name=str(_first_present(data, ("player", "player_name", "name"))),
        position=Position(str(data["position"]).upper()),
        innings=innings,
    )


def _first_present(data: dict[str, Any], keys: Iterable[str]) -> Any:
    for key in keys:
        if key in data:
            return data[key]
    raise ValueError(f"Missing one of: {', '.join(keys)}.")
