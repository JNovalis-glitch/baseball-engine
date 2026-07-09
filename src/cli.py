"""Command-line entry point for the baseball engine."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from adjustments import PositionRequest, apply_position_requests
from explain import explain_lineup, format_explanation
from game_plan import load_game_plan
from generator import generate_lineup
from lineup_io import format_tsv_lineup, parse_tsv_lineup
from models import Position
from validator import validate_lineup


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate or validate lineup cards.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    generate_parser = subparsers.add_parser("generate", help="Generate a lineup from a JSON game plan.")
    generate_parser.add_argument("game_plan", help="Path to game-plan JSON.")

    validate_parser = subparsers.add_parser("validate", help="Validate a pasted TSV lineup card.")
    validate_parser.add_argument("lineup_tsv", help="Path to TSV lineup card, or '-' to read pasted TSV from stdin.")
    validate_parser.add_argument("--game-plan", help="Optional JSON game plan for roster metadata and locks.")

    adjust_parser = subparsers.add_parser("adjust", help="Make small valid swaps for coach requests.")
    adjust_parser.add_argument("lineup_tsv", help="Path to TSV lineup card, or '-' to read pasted TSV from stdin.")
    adjust_parser.add_argument("--game-plan", required=True, help="JSON game plan for roster metadata and locks.")
    adjust_parser.add_argument(
        "--request",
        action="append",
        required=True,
        help="Position request in PLAYER:POSITION:COUNT form, e.g. Dillon:3B:1.",
    )

    args = parser.parse_args()
    if args.command == "generate":
        _generate(args.game_plan)
    elif args.command == "validate":
        _validate(args.lineup_tsv, args.game_plan)
    elif args.command == "adjust":
        _adjust(args.lineup_tsv, args.game_plan, args.request)


def _generate(game_plan_path: str) -> None:
    game_plan = load_game_plan(game_plan_path)
    generated = generate_lineup(
        game_plan.players,
        game_plan.locks,
        preferences=game_plan.preferences,
    )
    explanation = explain_lineup(
        generated.lineup,
        game_plan.players,
        generated.report,
        game_plan.locks,
    )

    print(format_tsv_lineup(generated.lineup))
    print()
    print(format_explanation(explanation))


def _validate(lineup_path: str, game_plan_path: str | None) -> None:
    lineup = parse_tsv_lineup(_read_text(lineup_path))
    if game_plan_path:
        game_plan = load_game_plan(game_plan_path)
        roster = game_plan.players
        locks = game_plan.locks
    else:
        roster = None
        locks = ()

    report = validate_lineup(lineup, roster=roster, locks=locks)
    _print_validation_report(report)


def _adjust(lineup_path: str, game_plan_path: str, raw_requests: list[str]) -> None:
    lineup = parse_tsv_lineup(_read_text(lineup_path))
    game_plan = load_game_plan(game_plan_path)
    requests = [_parse_request(value) for value in raw_requests]
    result = apply_position_requests(
        lineup,
        requests,
        roster=game_plan.players,
        locks=game_plan.locks,
    )

    print(format_tsv_lineup(result.lineup))
    print()
    if result.changes:
        print("Changes:")
        for change in result.changes:
            print(f"- {change}")
    else:
        print("No changes needed.")
    print()
    if result.satisfied:
        print("Adjustment passes hard validation.")
    else:
        print("Could not satisfy all requests without breaking hard validation.")
    for issue in result.report.issues:
        print(f"{issue.severity.value.upper()}: {issue.code}: {issue.message}")


def _read_text(path: str) -> str:
    if path == "-":
        return sys.stdin.read()
    return Path(path).read_text(encoding="utf-8")


def _print_validation_report(report) -> None:
    if report.ok:
        print("Lineup passes hard validation.")
    else:
        print(f"Lineup has {len(report.errors)} hard validation error(s).")

    if report.errors:
        print()
        print("Errors:")
        for issue in report.errors:
            print(f"- {issue.code}: {issue.message}")

    if report.warnings:
        print()
        print("Warnings:")
        for issue in report.warnings:
            print(f"- {issue.code}: {issue.message}")

    if report.ok and not report.warnings:
        print("No warnings.")


def _parse_request(value: str) -> PositionRequest:
    pieces = value.split(":")
    if len(pieces) not in {2, 3}:
        raise ValueError("Requests must use PLAYER:POSITION or PLAYER:POSITION:COUNT.")
    player_name = pieces[0]
    position = Position(pieces[1].upper())
    count = int(pieces[2]) if len(pieces) == 3 else 1
    return PositionRequest(player_name, position, count)


if __name__ == "__main__":
    main()
