"""Small coach-requested lineup adjustments."""
from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from typing import Dict, Iterable, List, Mapping, Sequence

from lineup_io import POSITION_ORDER
from models import Player, Position
from rules import DEFAULT_RULES, EngineRules
from validator import PositionLock, ValidationReport, validate_lineup


@dataclass(frozen=True)
class PositionRequest:
    player_name: str
    position: Position
    count: int = 1
    innings: tuple[int, ...] = ()


@dataclass(frozen=True)
class AdjustmentResult:
    lineup: Dict[Position, List[List[str]]]
    report: ValidationReport
    changes: tuple[str, ...]
    satisfied: bool


def apply_position_requests(
    lineup: Mapping[Position, Sequence[Sequence[str]]],
    requests: Iterable[PositionRequest],
    roster: Iterable[Player | str] | None = None,
    locks: Iterable[PositionLock] = (),
    rules: EngineRules = DEFAULT_RULES,
) -> AdjustmentResult:
    current = _copy_lineup(lineup)
    locks = tuple(locks)
    changes: List[str] = []

    for request in requests:
        while _request_count(current, request, rules) < request.count:
            candidate = _best_single_swap(current, request, roster, locks, rules)
            if candidate is None:
                report = validate_lineup(current, roster=roster, locks=locks, rules=rules)
                return AdjustmentResult(current, report, tuple(changes), False)
            current, description = candidate
            changes.append(description)

    report = validate_lineup(current, roster=roster, locks=locks, rules=rules)
    return AdjustmentResult(current, report, tuple(changes), report.ok)


def _best_single_swap(
    lineup: Dict[Position, List[List[str]]],
    request: PositionRequest,
    roster: Iterable[Player | str] | None,
    locks: Sequence[PositionLock],
    rules: EngineRules,
) -> tuple[Dict[Position, List[List[str]]], str] | None:
    best: tuple[int, Dict[Position, List[List[str]]], str] | None = None
    allowed_innings = request.innings or tuple(range(1, rules.innings + 1))

    for inning in allowed_innings:
        current_position = _position_for_player(lineup, request.player_name, inning)
        if current_position is None or current_position is Position.BENCH:
            continue
        if current_position is request.position:
            continue
        if _is_locked(request.player_name, inning, locks):
            continue
        target_player = _single_at(lineup, request.position, inning)
        if not target_player or _is_locked(target_player, inning, locks):
            continue

        candidate = _copy_lineup(lineup)
        candidate[current_position][inning - 1] = [target_player]
        candidate[request.position][inning - 1] = [request.player_name]
        report = validate_lineup(candidate, roster=roster, locks=locks, rules=rules)
        if not report.ok:
            continue

        cost = _swap_cost(lineup, candidate, inning, request.player_name, target_player)
        description = (
            f"Swapped {request.player_name} from {current_position.value} to "
            f"{request.position.value} in inning {inning}; {target_player} moved to "
            f"{current_position.value}."
        )
        if best is None or cost < best[0]:
            best = (cost, candidate, description)

    if best is None:
        return None
    return best[1], best[2]


def _request_count(
    lineup: Mapping[Position, Sequence[Sequence[str]]],
    request: PositionRequest,
    rules: EngineRules,
) -> int:
    innings = request.innings or tuple(range(1, rules.innings + 1))
    return sum(
        1
        for inning in innings
        if request.player_name in lineup[request.position][inning - 1]
    )


def _swap_cost(
    original: Mapping[Position, Sequence[Sequence[str]]],
    candidate: Mapping[Position, Sequence[Sequence[str]]],
    inning: int,
    requested_player: str,
    swapped_player: str,
) -> int:
    cost = 0
    for name in (requested_player, swapped_player):
        before = _position_for_player(original, name, inning)
        after = _position_for_player(candidate, name, inning)
        if before != after:
            cost += 1
    return cost


def _copy_lineup(
    lineup: Mapping[Position, Sequence[Sequence[str]]],
) -> Dict[Position, List[List[str]]]:
    return {
        position: [list(names) for names in innings]
        for position, innings in deepcopy(dict(lineup)).items()
    }


def _position_for_player(
    lineup: Mapping[Position, Sequence[Sequence[str]]],
    player_name: str,
    inning: int,
) -> Position | None:
    for position in POSITION_ORDER + [Position.BENCH]:
        if player_name in lineup[position][inning - 1]:
            return position
    return None


def _single_at(
    lineup: Mapping[Position, Sequence[Sequence[str]]],
    position: Position,
    inning: int,
) -> str:
    names = lineup[position][inning - 1]
    return names[0] if names else ""


def _is_locked(
    player_name: str,
    inning: int,
    locks: Sequence[PositionLock],
) -> bool:
    return any(lock.player_name == player_name and lock.inning == inning for lock in locks)
