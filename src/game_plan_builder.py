"""Build game-plan JSON from coach-friendly text input."""
from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Iterable, List

from models import Position, Tier


@dataclass(frozen=True)
class PlayerInput:
    source_name: str
    card_name: str
    tier: Tier = Tier.B
    pitcher: bool = False
    catcher: bool = False
    new_player: bool = False
    active: bool = True


def build_game_plan_data(
    roster_text: str,
    pitcher_locks: Iterable[str] = (),
    catcher_locks: Iterable[str] = (),
    top_defenders: Iterable[str] = (),
    development_focus: Iterable[str] = (),
    avoid_positions: Iterable[str] = (),
    name_style: str = "first",
) -> dict:
    players = parse_roster_text(roster_text, name_style=name_style)
    locks = [
        _parse_lock(value, Position.P)
        for value in pitcher_locks
    ] + [
        _parse_lock(value, Position.C)
        for value in catcher_locks
    ]

    pitcher_names = {lock["player"] for lock in locks if lock["position"] == Position.P.value}
    catcher_names = {lock["player"] for lock in locks if lock["position"] == Position.C.value}

    return {
        "players": [
            {
                "name": player.card_name,
                "tier": player.tier.value,
                "pitcher": player.pitcher or player.card_name in pitcher_names,
                "catcher": player.catcher or player.card_name in catcher_names,
                "new_player": player.new_player,
                "active": player.active,
            }
            for player in players
        ],
        "locks": locks,
        "preferences": {
            "top_defenders": list(top_defenders),
            "development_focus": list(development_focus),
            "spread_first_inning_infield_strength": True,
            "protect_final_inning_top_defenders": True,
            "avoid_top_shortstop_in_kid_pitch": True,
            "prefer_infield_after_outfield_bench": True,
            "avoid_positions": [
                _parse_avoidance(value)
                for value in avoid_positions
            ],
        },
    }


def build_game_plan_json(*args, **kwargs) -> str:
    return json.dumps(build_game_plan_data(*args, **kwargs), indent=2) + "\n"


def parse_roster_text(roster_text: str, name_style: str = "first") -> List[PlayerInput]:
    players = []
    for raw_line in roster_text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if line.lower().startswith(("position", "bench", "wednesday", "thursday", "friday")):
            continue
        players.append(_parse_roster_line(line, name_style))
    if not players:
        raise ValueError("Roster input did not include any players.")
    return players


def _parse_roster_line(line: str, name_style: str) -> PlayerInput:
    pieces = [piece.strip() for piece in line.split("|")]
    source_name = pieces[0]
    card_name = pieces[1] if len(pieces) > 1 and pieces[1] else _card_name(source_name, name_style)
    tier = Tier(pieces[2].upper()) if len(pieces) > 2 and pieces[2] else Tier.B
    flags = _flags(pieces[3] if len(pieces) > 3 else "")
    return PlayerInput(
        source_name=source_name,
        card_name=card_name,
        tier=tier,
        pitcher="pitcher" in flags or "p" in flags,
        catcher="catcher" in flags or "c" in flags,
        new_player="new" in flags,
        active="inactive" not in flags,
    )


def _card_name(source_name: str, name_style: str) -> str:
    if name_style == "full":
        return source_name
    if name_style != "first":
        raise ValueError("name_style must be 'first' or 'full'.")
    return source_name.split()[0]


def _parse_lock(value: str, position: Position) -> dict:
    pieces = [piece.strip() for piece in value.split(":")]
    if len(pieces) != 2:
        raise ValueError("Locks must use PLAYER:INNING, for example Weston:3.")
    return {
        "inning": int(pieces[1]),
        "position": position.value,
        "player": pieces[0],
    }


def _parse_avoidance(value: str) -> dict:
    pieces = [piece.strip() for piece in value.split(":")]
    if len(pieces) not in {2, 3}:
        raise ValueError("Avoidance must use PLAYER:POSITION or PLAYER:POSITION:INNING.")
    data = {
        "player": pieces[0],
        "position": Position(pieces[1].upper()).value,
    }
    if len(pieces) == 3:
        data["innings"] = [int(pieces[2])]
    return data


def _flags(value: str) -> set[str]:
    return {
        flag.strip().lower()
        for flag in value.replace(",", " ").split()
        if flag.strip()
    }
