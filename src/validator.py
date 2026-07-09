"""Validation for completed lineup cards."""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

from lineup_io import POSITION_ORDER
from models import Player, Position, Tier
from rules import DEFAULT_RULES, EngineRules


OUTFIELD_POSITIONS = {Position.LF, Position.LCF, Position.RCF, Position.RF}


class Severity(Enum):
    ERROR = "error"
    WARNING = "warning"


@dataclass(frozen=True)
class PositionLock:
    inning: int
    position: Position
    player_name: str


@dataclass(frozen=True)
class ValidationIssue:
    severity: Severity
    code: str
    message: str
    inning: Optional[int] = None
    player_name: Optional[str] = None


@dataclass(frozen=True)
class ValidationReport:
    issues: Tuple[ValidationIssue, ...]

    @property
    def errors(self) -> Tuple[ValidationIssue, ...]:
        return tuple(issue for issue in self.issues if issue.severity is Severity.ERROR)

    @property
    def warnings(self) -> Tuple[ValidationIssue, ...]:
        return tuple(issue for issue in self.issues if issue.severity is Severity.WARNING)

    @property
    def ok(self) -> bool:
        return not self.errors


def validate_lineup(
    lineup: Mapping[Position, Sequence[Sequence[str]]],
    roster: Optional[Iterable[Player | str]] = None,
    locks: Iterable[PositionLock] = (),
    rules: EngineRules = DEFAULT_RULES,
) -> ValidationReport:
    issues: List[ValidationIssue] = []
    player_names, players_by_name = _roster_names(roster, lineup)
    innings = rules.innings

    _validate_shape(lineup, innings, issues)

    for inning in range(1, innings + 1):
        fielders = _fielders_for_inning(lineup, inning)
        bench = _bench_for_inning(lineup, inning)
        all_names = fielders + bench

        if len(fielders) != rules.players_on_field:
            issues.append(_error(
                "wrong_fielder_count",
                f"Inning {inning} has {len(fielders)} fielders; expected {rules.players_on_field}.",
                inning,
            ))
        if len(bench) != rules.bench_per_inning:
            issues.append(_error(
                "wrong_bench_count",
                f"Inning {inning} has {len(bench)} bench players; expected {rules.bench_per_inning}.",
                inning,
            ))

        duplicates = _duplicates(all_names)
        for name in duplicates:
            issues.append(_error(
                "duplicate_player",
                f"Inning {inning} has {name} assigned more than once.",
                inning,
                name,
            ))

        missing = sorted(player_names - set(all_names))
        for name in missing:
            issues.append(_error(
                "missing_player",
                f"Inning {inning} is missing {name}.",
                inning,
                name,
            ))

    _validate_bench(lineup, player_names, players_by_name, rules, issues)
    _validate_outfield_patterns(lineup, player_names, rules, issues)
    _validate_locks(lineup, locks, issues)
    _validate_first_base(lineup, players_by_name, rules, issues)
    _validate_development_variety(lineup, players_by_name, rules, issues)

    return ValidationReport(tuple(issues))


def _validate_shape(
    lineup: Mapping[Position, Sequence[Sequence[str]]],
    innings: int,
    issues: List[ValidationIssue],
) -> None:
    for position in POSITION_ORDER + [Position.BENCH]:
        if position not in lineup:
            issues.append(_error("missing_position", f"Lineup is missing {position.value}."))
            continue
        if len(lineup[position]) != innings:
            issues.append(_error(
                "wrong_inning_count",
                f"{position.value} has {len(lineup[position])} innings; expected {innings}.",
            ))


def _validate_bench(
    lineup: Mapping[Position, Sequence[Sequence[str]]],
    player_names: set[str],
    players_by_name: Mapping[str, Player],
    rules: EngineRules,
    issues: List[ValidationIssue],
) -> None:
    for name in sorted(player_names):
        bench_innings = [
            inning
            for inning in range(1, rules.innings + 1)
            if name in _bench_for_inning(lineup, inning)
        ]
        if len(bench_innings) > rules.max_bench_per_player:
            issues.append(_error(
                "too_many_bench",
                f"{name} sits {len(bench_innings)} times: {bench_innings}.",
                player_name=name,
            ))
        if len(bench_innings) < rules.max_bench_per_player:
            issues.append(_error(
                "too_few_bench",
                f"{name} sits {len(bench_innings)} times; expected {rules.max_bench_per_player}.",
                player_name=name,
            ))
        for earlier, later in zip(bench_innings, bench_innings[1:]):
            if later == earlier + 1:
                issues.append(_error(
                    "consecutive_bench",
                    f"{name} sits in back-to-back innings {earlier} and {later}.",
                    later,
                    name,
                ))
        player = players_by_name.get(name)
        if (
            rules.no_new_player_bench_first
            and player
            and player.new_player
            and 1 in bench_innings
        ):
            issues.append(_error(
                "new_player_benched_first",
                f"{name} is a new player and should not sit the 1st inning.",
                1,
                name,
            ))


def _validate_outfield_patterns(
    lineup: Mapping[Position, Sequence[Sequence[str]]],
    player_names: set[str],
    rules: EngineRules,
    issues: List[ValidationIssue],
) -> None:
    if not rules.no_consecutive_outfield:
        return
    for name in sorted(player_names):
        outfield_innings = [
            inning
            for inning, position in _player_positions(lineup, name, rules.innings)
            if position in OUTFIELD_POSITIONS
        ]
        for earlier, later in zip(outfield_innings, outfield_innings[1:]):
            if later == earlier + 1:
                issues.append(_error(
                    "consecutive_outfield",
                    f"{name} plays outfield in back-to-back innings {earlier} and {later}.",
                    later,
                    name,
                ))


def _validate_locks(
    lineup: Mapping[Position, Sequence[Sequence[str]]],
    locks: Iterable[PositionLock],
    issues: List[ValidationIssue],
) -> None:
    for lock in locks:
        assigned = _single_at(lineup, lock.position, lock.inning)
        if assigned != lock.player_name:
            issues.append(_error(
                "lock_broken",
                f"Inning {lock.inning} {lock.position.value} is {assigned or 'empty'}; expected {lock.player_name}.",
                lock.inning,
                lock.player_name,
            ))


def _validate_first_base(
    lineup: Mapping[Position, Sequence[Sequence[str]]],
    players_by_name: Mapping[str, Player],
    rules: EngineRules,
    issues: List[ValidationIssue],
) -> None:
    if not rules.first_base_prefers_tier_a or not players_by_name:
        return
    for inning in range(1, rules.innings + 1):
        name = _single_at(lineup, Position.FIRST, inning)
        player = players_by_name.get(name)
        if player and player.tier is not Tier.A:
            issues.append(_error(
                "ineligible_first_base",
                f"Inning {inning} has {name} at 1B, but only A players are eligible.",
                inning,
                name,
            ))


def _validate_development_variety(
    lineup: Mapping[Position, Sequence[Sequence[str]]],
    players_by_name: Mapping[str, Player],
    rules: EngineRules,
    issues: List[ValidationIssue],
) -> None:
    if not rules.diversify_development_positions or not players_by_name:
        return
    for name, player in sorted(players_by_name.items()):
        if player.tier is Tier.A:
            continue
        positions = [
            position
            for _, position in _player_positions(lineup, name, rules.innings)
            if position is not Position.BENCH
        ]
        outfield_counts: Dict[Position, int] = {}
        for position in positions:
            if position in OUTFIELD_POSITIONS:
                outfield_counts[position] = outfield_counts.get(position, 0) + 1
        for position, count in sorted(outfield_counts.items(), key=lambda item: item[0].value):
            if count > rules.max_same_outfield_position_per_player:
                issues.append(_warning(
                    "repeated_outfield_position",
                    f"{name} plays {position.value} {count} times; prefer a different corner/infield look if practical.",
                    player_name=name,
                ))


def _roster_names(
    roster: Optional[Iterable[Player | str]],
    lineup: Mapping[Position, Sequence[Sequence[str]]],
) -> Tuple[set[str], Dict[str, Player]]:
    players_by_name: Dict[str, Player] = {}
    if roster is not None:
        names = set()
        for item in roster:
            if isinstance(item, Player):
                names.add(item.name)
                players_by_name[item.name] = item
            else:
                names.add(item)
        return names, players_by_name

    names = {
        name
        for innings in lineup.values()
        for names_for_inning in innings
        for name in names_for_inning
    }
    return names, players_by_name


def _fielders_for_inning(
    lineup: Mapping[Position, Sequence[Sequence[str]]],
    inning: int,
) -> List[str]:
    return [
        name
        for position in POSITION_ORDER
        for name in _names_at(lineup, position, inning)
    ]


def _bench_for_inning(
    lineup: Mapping[Position, Sequence[Sequence[str]]],
    inning: int,
) -> List[str]:
    return _names_at(lineup, Position.BENCH, inning)


def _names_at(
    lineup: Mapping[Position, Sequence[Sequence[str]]],
    position: Position,
    inning: int,
) -> List[str]:
    innings = lineup.get(position, [])
    if inning < 1 or inning > len(innings):
        return []
    return list(innings[inning - 1])


def _single_at(
    lineup: Mapping[Position, Sequence[Sequence[str]]],
    position: Position,
    inning: int,
) -> str:
    names = _names_at(lineup, position, inning)
    return names[0] if names else ""


def _player_positions(
    lineup: Mapping[Position, Sequence[Sequence[str]]],
    player_name: str,
    innings: int,
) -> List[Tuple[int, Position]]:
    result = []
    for inning in range(1, innings + 1):
        found = Position.BENCH
        for position in POSITION_ORDER:
            if player_name in _names_at(lineup, position, inning):
                found = position
                break
        result.append((inning, found))
    return result


def _duplicates(names: Sequence[str]) -> List[str]:
    return sorted({name for name in names if names.count(name) > 1})


def _error(
    code: str,
    message: str,
    inning: Optional[int] = None,
    player_name: Optional[str] = None,
) -> ValidationIssue:
    return ValidationIssue(Severity.ERROR, code, message, inning, player_name)


def _warning(
    code: str,
    message: str,
    inning: Optional[int] = None,
    player_name: Optional[str] = None,
) -> ValidationIssue:
    return ValidationIssue(Severity.WARNING, code, message, inning, player_name)
