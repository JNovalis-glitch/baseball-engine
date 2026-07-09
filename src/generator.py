"""Deterministic first-pass lineup generation."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List, Mapping, Sequence

from lineup_io import POSITION_ORDER
from models import Player, Position, Tier
from preferences import CoachPreferences
from rules import DEFAULT_RULES, EngineRules
from validator import OUTFIELD_POSITIONS, PositionLock, ValidationReport, validate_lineup


COACH_PITCH_PRIORITY = [
    Position.FIRST,
    Position.SHORT,
    Position.P,
    Position.LCF,
    Position.LF,
    Position.THIRD,
    Position.SECOND,
    Position.RCF,
    Position.RF,
    Position.C,
]

KID_PITCH_PRIORITY = [
    Position.P,
    Position.C,
    Position.FIRST,
    Position.SHORT,
    Position.THIRD,
    Position.SECOND,
    Position.LCF,
    Position.LF,
    Position.RCF,
    Position.RF,
]


@dataclass(frozen=True)
class GeneratedLineup:
    lineup: Dict[Position, List[List[str]]]
    report: ValidationReport


def generate_lineup(
    roster: Sequence[Player],
    locks: Iterable[PositionLock] = (),
    rules: EngineRules = DEFAULT_RULES,
    preferences: CoachPreferences = CoachPreferences(),
) -> GeneratedLineup:
    """Generate a complete lineup and validate it.

    This is intentionally deterministic. It builds the card in the same order
    coaches do by hand: bench, locked batteries, pitcher/catcher, then the
    remaining field positions.
    """
    locks = tuple(locks)
    active_roster = [player for player in roster if player.active]
    _validate_roster_size(active_roster, rules)

    lineup = _empty_lineup(rules)
    _assign_bench(lineup, active_roster, locks, rules, preferences)
    _apply_locks(lineup, locks)
    _assign_pitchers_and_catchers(lineup, active_roster, rules, preferences)
    _assign_fielders(lineup, active_roster, rules, preferences)

    report = validate_lineup(lineup, roster=active_roster, locks=locks, rules=rules)
    return GeneratedLineup(lineup, report)


def _validate_roster_size(roster: Sequence[Player], rules: EngineRules) -> None:
    expected = rules.players_on_field + rules.bench_per_inning
    if len(roster) != expected:
        raise ValueError(f"Expected {expected} active players; got {len(roster)}.")


def _empty_lineup(rules: EngineRules) -> Dict[Position, List[List[str]]]:
    return {
        position: [[] for _ in range(rules.innings)]
        for position in POSITION_ORDER + [Position.BENCH]
    }


def _assign_bench(
    lineup: Dict[Position, List[List[str]]],
    roster: Sequence[Player],
    locks: Sequence[PositionLock],
    rules: EngineRules,
    preferences: CoachPreferences,
) -> None:
    locked_by_inning = _locked_players_by_inning(locks)
    benched: set[str] = set()

    for inning in range(1, rules.innings + 1):
        while len(lineup[Position.BENCH][inning - 1]) < rules.bench_per_inning:
            candidates = [
                player
                for player in roster
                if player.name not in benched
                and player.name not in locked_by_inning.get(inning, set())
                and not (
                    inning == 1
                    and rules.no_new_player_bench_first
                    and player.new_player
                )
            ]
            if not candidates:
                candidates = [
                    player
                    for player in roster
                    if player.name not in benched
                    and player.name not in locked_by_inning.get(inning, set())
                ]
            if not candidates:
                raise ValueError(f"Could not fill bench for inning {inning}.")

            player = min(candidates, key=lambda item: _bench_score(item, inning, preferences))
            lineup[Position.BENCH][inning - 1].append(player.name)
            benched.add(player.name)


def _bench_score(
    player: Player,
    inning: int,
    preferences: CoachPreferences,
) -> tuple[int, int, str]:
    tier_penalty = {Tier.C: 0, Tier.B: 1, Tier.A: 2}[player.tier]
    first_inning_penalty = 10 if inning == 1 and player.tier is Tier.A else 0
    top_defender_penalty = 4 if player.name in preferences.top_defenders else 0
    return (first_inning_penalty + tier_penalty + top_defender_penalty, inning, player.name)


def _apply_locks(
    lineup: Dict[Position, List[List[str]]],
    locks: Sequence[PositionLock],
) -> None:
    for lock in locks:
        lineup[lock.position][lock.inning - 1] = [lock.player_name]


def _assign_pitchers_and_catchers(
    lineup: Dict[Position, List[List[str]]],
    roster: Sequence[Player],
    rules: EngineRules,
    preferences: CoachPreferences,
) -> None:
    for inning in range(1, rules.innings + 1):
        if not lineup[Position.P][inning - 1]:
            lineup[Position.P][inning - 1] = [
                _choose_player(
                    roster,
                    lineup,
                    inning,
                    Position.P,
                    rules,
                    preferences,
                    preferred=lambda player: player.pitcher or player.tier is Tier.A,
                ).name
            ]
        if not lineup[Position.C][inning - 1]:
            lineup[Position.C][inning - 1] = [
                _choose_player(
                    roster,
                    lineup,
                    inning,
                    Position.C,
                    rules,
                    preferences,
                    preferred=lambda player: player.catcher or player.tier is Tier.A,
                ).name
            ]


def _assign_fielders(
    lineup: Dict[Position, List[List[str]]],
    roster: Sequence[Player],
    rules: EngineRules,
    preferences: CoachPreferences,
) -> None:
    for inning in range(1, rules.innings + 1):
        order = (
            KID_PITCH_PRIORITY
            if inning in rules.kid_pitch_innings
            else COACH_PITCH_PRIORITY
        )
        empty_positions = [
            position for position in order if not lineup[position][inning - 1]
        ]
        assignment = _best_assignment_for_inning(
            roster,
            lineup,
            inning,
            empty_positions,
            rules,
            preferences,
            enforce_outfield_rest=True,
        )
        if assignment is None:
            assignment = _best_assignment_for_inning(
                roster,
                lineup,
                inning,
                empty_positions,
                rules,
                preferences,
                enforce_outfield_rest=False,
            )
        if assignment is None:
            raise ValueError(f"Could not assign fielders for inning {inning}.")
        for position, player_name in assignment.items():
            lineup[position][inning - 1] = [player_name]


def _best_assignment_for_inning(
    roster: Sequence[Player],
    lineup: Mapping[Position, Sequence[Sequence[str]]],
    inning: int,
    positions: Sequence[Position],
    rules: EngineRules,
    preferences: CoachPreferences,
    enforce_outfield_rest: bool,
) -> Dict[Position, str] | None:
    best: tuple[int, Dict[Position, str]] | None = None
    current: Dict[Position, str] = {}
    assigned = set(_assigned_names(lineup, inning))
    bench = set(lineup[Position.BENCH][inning - 1])

    def search(index: int, score: int) -> None:
        nonlocal best
        if best and score >= best[0]:
            return
        if index == len(positions):
            best = (score, dict(current))
            return

        position = positions[index]
        for player in _ranked_candidates(
            roster,
            lineup,
            inning,
            position,
            assigned,
            bench,
            rules,
            preferences,
            enforce_outfield_rest,
        ):
            assigned.add(player.name)
            current[position] = player.name
            position_score = _position_score(player, position, inning, lineup, rules, preferences)
            search(index + 1, score + position_score[0])
            current.pop(position)
            assigned.remove(player.name)

    search(0, 0)
    return best[1] if best else None


def _ranked_candidates(
    roster: Sequence[Player],
    lineup: Mapping[Position, Sequence[Sequence[str]]],
    inning: int,
    position: Position,
    assigned: set[str],
    bench: set[str],
    rules: EngineRules,
    preferences: CoachPreferences,
    enforce_outfield_rest: bool,
) -> List[Player]:
    candidates = [
        player
        for player in roster
        if player.name not in assigned
        and player.name not in bench
        and _eligible_for_position(player, position, inning, rules, preferences)
        and not (
            enforce_outfield_rest
            and position in OUTFIELD_POSITIONS
            and _played_outfield_previous_inning(lineup, player.name, inning)
        )
    ]
    return sorted(
        candidates,
        key=lambda player: _position_score(player, position, inning, lineup, rules, preferences),
    )


def _choose_player(
    roster: Sequence[Player],
    lineup: Mapping[Position, Sequence[Sequence[str]]],
    inning: int,
    position: Position,
    rules: EngineRules,
    preferences: CoachPreferences,
    preferred=lambda player: True,
) -> Player:
    assigned = set(_assigned_names(lineup, inning))
    candidates = [
        player
        for player in roster
        if player.name not in assigned
        and not _is_benched(lineup, player.name, inning)
        and _eligible_for_position(player, position, inning, rules, preferences)
    ]
    if not candidates:
        raise ValueError(f"No eligible candidates for {position.value} in inning {inning}.")

    preferred_candidates = [player for player in candidates if preferred(player)]
    if preferred_candidates:
        candidates = preferred_candidates

    return min(
        candidates,
        key=lambda player: _position_score(player, position, inning, lineup, rules, preferences),
    )


def _position_score(
    player: Player,
    position: Position,
    inning: int,
    lineup: Mapping[Position, Sequence[Sequence[str]]],
    rules: EngineRules,
    preferences: CoachPreferences,
) -> tuple[int, int, str]:
    score = 0
    history = _history(lineup, player.name, inning - 1)

    if position in {Position.FIRST, Position.SHORT, Position.P, Position.LCF}:
        score += {Tier.A: 0, Tier.B: 8, Tier.C: 16}[player.tier]
        if player.name in preferences.top_defenders:
            score -= 4
    elif position in {Position.SECOND, Position.THIRD, Position.LF, Position.RF}:
        score += {Tier.C: 0, Tier.B: 2, Tier.A: 5}[player.tier]

    if (
        inning == 1
        and preferences.spread_first_inning_infield_strength
        and player.name in preferences.top_defenders
        and position in {Position.SECOND, Position.THIRD}
    ):
        score += 8
    if (
        inning == 1
        and preferences.spread_first_inning_infield_strength
        and player.name not in preferences.top_defenders
        and position in {Position.SECOND, Position.THIRD}
    ):
        score -= 3

    if position in OUTFIELD_POSITIONS:
        if history and history[-1] in OUTFIELD_POSITIONS:
            score += 100
        if _is_development_player(player, preferences):
            score += 10 * history.count(position)
            if position in {Position.LF, Position.RF}:
                score -= 2
    elif position is Position.THIRD and _is_development_player(player, preferences):
        score -= 2

    score += 3 * history.count(position)
    score += _total_assignments(history)
    return (score, len(history), player.name)


def _eligible_for_position(
    player: Player,
    position: Position,
    inning: int,
    rules: EngineRules,
    preferences: CoachPreferences,
) -> bool:
    if position is Position.FIRST and rules.first_base_prefers_tier_a:
        return player.tier is Tier.A
    if any(
        avoidance.applies_to(player.name, position, inning)
        for avoidance in preferences.avoid_positions
    ):
        return False
    return True


def _is_development_player(player: Player, preferences: CoachPreferences) -> bool:
    return player.tier is not Tier.A or player.name in preferences.development_focus


def _assigned_names(
    lineup: Mapping[Position, Sequence[Sequence[str]]],
    inning: int,
) -> List[str]:
    return [
        name
        for position in POSITION_ORDER
        for name in lineup[position][inning - 1]
    ]


def _is_benched(
    lineup: Mapping[Position, Sequence[Sequence[str]]],
    player_name: str,
    inning: int,
) -> bool:
    return player_name in lineup[Position.BENCH][inning - 1]


def _played_outfield_previous_inning(
    lineup: Mapping[Position, Sequence[Sequence[str]]],
    player_name: str,
    inning: int,
) -> bool:
    if inning <= 1:
        return False
    return any(
        player_name in lineup[position][inning - 2]
        for position in OUTFIELD_POSITIONS
    )


def _history(
    lineup: Mapping[Position, Sequence[Sequence[str]]],
    player_name: str,
    through_inning: int,
) -> List[Position]:
    positions = []
    for inning in range(1, through_inning + 1):
        for position in POSITION_ORDER:
            if player_name in lineup[position][inning - 1]:
                positions.append(position)
                break
    return positions


def _total_assignments(history: Sequence[Position]) -> int:
    return len([position for position in history if position is not Position.BENCH])


def _locked_players_by_inning(
    locks: Sequence[PositionLock],
) -> Dict[int, set[str]]:
    result: Dict[int, set[str]] = {}
    for lock in locks:
        result.setdefault(lock.inning, set()).add(lock.player_name)
    return result
