"""Coach-readable lineup explanations."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Mapping, Sequence

from lineup_io import POSITION_ORDER, inning_label
from models import Player, Position, Tier
from validator import OUTFIELD_POSITIONS, PositionLock, ValidationReport


PRIORITY_POSITIONS = {Position.P, Position.C, Position.FIRST, Position.SHORT, Position.LCF}


@dataclass(frozen=True)
class PlayerSummary:
    player_name: str
    positions: tuple[str, ...]
    bench_innings: tuple[int, ...]
    outfield_innings: tuple[int, ...]


@dataclass(frozen=True)
class LineupExplanation:
    lines: tuple[str, ...]
    player_summaries: tuple[PlayerSummary, ...]


def explain_lineup(
    lineup: Mapping[Position, Sequence[Sequence[str]]],
    roster: Iterable[Player | str],
    report: ValidationReport,
    locks: Iterable[PositionLock] = (),
) -> LineupExplanation:
    roster_list = list(roster)
    names = sorted(_player_name(player) for player in roster_list)
    player_by_name = {
        player.name: player for player in roster_list if isinstance(player, Player)
    }
    innings = len(lineup[Position.P])

    lines: List[str] = []
    if report.ok:
        lines.append("Hard validation passes.")
    else:
        lines.append(f"Hard validation has {len(report.errors)} error(s).")
    if report.warnings:
        lines.append(f"Soft validation has {len(report.warnings)} warning(s).")

    lock_lines = _lock_lines(lineup, locks)
    if lock_lines:
        lines.extend(lock_lines)

    lines.extend(_bench_lines(lineup, names, innings))
    lines.extend(_pattern_lines(lineup, names, player_by_name, innings))

    summaries = tuple(_player_summary(lineup, name, innings) for name in names)
    return LineupExplanation(tuple(lines), summaries)


def format_explanation(explanation: LineupExplanation) -> str:
    lines = list(explanation.lines)
    lines.append("")
    lines.append("Player paths:")
    for summary in explanation.player_summaries:
        path = " / ".join(summary.positions)
        lines.append(f"- {summary.player_name}: {path}")
    return "\n".join(lines)


def _lock_lines(
    lineup: Mapping[Position, Sequence[Sequence[str]]],
    locks: Iterable[PositionLock],
) -> List[str]:
    lines = []
    for lock in locks:
        actual = _single_at(lineup, lock.position, lock.inning)
        if actual == lock.player_name:
            lines.append(
                f"Lock honored: {lock.player_name} at {lock.position.value} in the {inning_label(lock.inning)}."
            )
        else:
            lines.append(
                f"Lock broken: {lock.position.value} in the {inning_label(lock.inning)} is {actual or 'empty'}, expected {lock.player_name}."
            )
    return lines


def _bench_lines(lineup, names: Sequence[str], innings: int) -> List[str]:
    bench_counts = {
        name: [inning for inning in range(1, innings + 1) if name in lineup[Position.BENCH][inning - 1]]
        for name in names
    }
    if all(len(innings_sat) == 1 for innings_sat in bench_counts.values()):
        return ["Bench is balanced: every player sits exactly once."]
    return [
        "Bench needs review: "
        + ", ".join(f"{name} sits {innings_sat}" for name, innings_sat in bench_counts.items())
    ]


def _pattern_lines(lineup, names: Sequence[str], player_by_name: Mapping[str, Player], innings: int) -> List[str]:
    lines = []
    top_paths = []
    development_paths = []
    for name in names:
        positions = _positions_for_player(lineup, name, innings)
        priority_count = sum(1 for position in positions if position in PRIORITY_POSITIONS)
        outfield_count = sum(1 for position in positions if position in OUTFIELD_POSITIONS)
        player = player_by_name.get(name)
        if player and player.tier is Tier.A and priority_count >= 3:
            top_paths.append(f"{name} anchors {priority_count} priority spots")
        if player and player.tier is not Tier.A:
            unique_positions = {position for position in positions if position is not Position.BENCH}
            if len(unique_positions) >= 4:
                development_paths.append(f"{name} gets {len(unique_positions)} different looks")
            elif outfield_count >= 3:
                development_paths.append(f"{name} may need more position variety")

    if top_paths:
        lines.append("Top defenders are used in priority roles: " + "; ".join(top_paths) + ".")
    if development_paths:
        lines.append("Development variety: " + "; ".join(development_paths) + ".")
    return lines


def _player_summary(lineup, name: str, innings: int) -> PlayerSummary:
    positions = tuple(_position_for_player(lineup, name, inning).value for inning in range(1, innings + 1))
    bench_innings = tuple(
        inning for inning in range(1, innings + 1)
        if _position_for_player(lineup, name, inning) is Position.BENCH
    )
    outfield_innings = tuple(
        inning for inning in range(1, innings + 1)
        if _position_for_player(lineup, name, inning) in OUTFIELD_POSITIONS
    )
    return PlayerSummary(name, positions, bench_innings, outfield_innings)


def _positions_for_player(lineup, name: str, innings: int) -> List[Position]:
    return [_position_for_player(lineup, name, inning) for inning in range(1, innings + 1)]


def _position_for_player(lineup, name: str, inning: int) -> Position:
    for position in POSITION_ORDER:
        if name in lineup[position][inning - 1]:
            return position
    return Position.BENCH


def _single_at(lineup, position: Position, inning: int) -> str:
    names = lineup[position][inning - 1]
    return names[0] if names else ""


def _player_name(player: Player | str) -> str:
    return player.name if isinstance(player, Player) else player
