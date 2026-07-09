"""Read and write coach-facing lineup cards."""
from __future__ import annotations

from typing import Dict, List

from models import Position


POSITION_ORDER = [
    Position.P,
    Position.C,
    Position.FIRST,
    Position.SECOND,
    Position.SHORT,
    Position.THIRD,
    Position.LF,
    Position.LCF,
    Position.RCF,
    Position.RF,
]


def inning_label(inning: int) -> str:
    suffix = "th"
    if inning % 10 == 1 and inning % 100 != 11:
        suffix = "st"
    elif inning % 10 == 2 and inning % 100 != 12:
        suffix = "nd"
    elif inning % 10 == 3 and inning % 100 != 13:
        suffix = "rd"
    return f"{inning}{suffix}"


def parse_tsv_lineup(text: str) -> Dict[Position, List[List[str]]]:
    """Parse the exact paste-from-Sheets format used by coaches.

    The returned mapping stores every position as a list by inning. Fielding
    positions contain one name per inning; BENCH contains a list of bench names
    per inning.
    """
    text = text.lstrip("\ufeff")
    rows = [
        [cell.strip() for cell in line.split("\t")]
        for line in text.strip().splitlines()
        if line.strip()
    ]
    if not rows:
        raise ValueError("Lineup is empty.")

    header = rows[0]
    if not header or header[0].lower() != "position":
        raise ValueError("First row must start with Position.")

    innings = len(header) - 1
    lineup: Dict[Position, List[List[str]]] = {
        position: [[] for _ in range(innings)]
        for position in POSITION_ORDER + [Position.BENCH]
    }

    bench_started = False
    for row in rows[1:]:
        if len(row) < innings + 1:
            row = row + [""] * (innings + 1 - len(row))

        label = row[0].strip()
        values = row[1 : innings + 1]
        if label:
            normalized = label.upper()
            if normalized == "BENCH":
                bench_started = True
                position = Position.BENCH
            else:
                position = Position(normalized)
                bench_started = False
        elif bench_started:
            position = Position.BENCH
        else:
            continue

        for inning_index, value in enumerate(values):
            if not value:
                continue
            if position is Position.BENCH:
                lineup[position][inning_index].append(value)
            else:
                lineup[position][inning_index] = [value]

    return lineup


def format_tsv_lineup(lineup: Dict[Position, List[List[str]]]) -> str:
    innings = len(lineup[Position.P])
    rows = [["Position", *[inning_label(i) for i in range(1, innings + 1)]]]

    for position in POSITION_ORDER:
        rows.append([position.value, *[_single_name(lineup[position][i]) for i in range(innings)]])

    max_bench_rows = max(len(names) for names in lineup[Position.BENCH])
    rows.append(["" for _ in range(innings + 1)])
    for bench_row in range(max_bench_rows):
        label = "Bench" if bench_row == 0 else ""
        rows.append([
            label,
            *[
                lineup[Position.BENCH][inning][bench_row]
                if bench_row < len(lineup[Position.BENCH][inning])
                else ""
                for inning in range(innings)
            ],
        ])

    return "\n".join("\t".join(row) for row in rows)


def _single_name(names: List[str]) -> str:
    return names[0] if names else ""
