from lineup_io import parse_tsv_lineup
from models import Position
from validator import PositionLock, validate_lineup


TONIGHT = """Position	1st	2nd	3rd	4th	5th	6th
P	Connor	Remy	James	Teddy	Weston	Auggie
C	Wesley	Bobby	Auggie	Connor	Killian	Remy
1B	James	Auggie	Connor	Weston	Teddy	James
2B	Dillon	River	Wesley	Remy	Miles	Bobby
SS	Teddy	Weston	Killian	Bobby	Auggie	Connor
3B	Killian	Miles	Teddy	Dillon	River	Dillon
LF	Bobby	Teddy	Weston	Miles	Remy	Weston
LCF	Auggie	James	Remy	James	Connor	Wesley
RCF	River	Wesley	River	Killian	Bobby	Miles
RF	Miles	Killian	Dillon	Wesley	Dillon	River
						
Bench	Remy	Dillon	Bobby	Auggie	Wesley	Killian
	Weston	Connor	Miles	River	James	Teddy
"""


LOCKS = [
    PositionLock(3, Position.P, "James"),
    PositionLock(3, Position.C, "Auggie"),
    PositionLock(4, Position.P, "Teddy"),
    PositionLock(4, Position.C, "Connor"),
]


def main() -> None:
    lineup = parse_tsv_lineup(TONIGHT)
    report = validate_lineup(lineup, locks=LOCKS)
    if report.ok:
        print("Lineup passes hard validation.")
    else:
        print("Lineup has validation errors.")

    for issue in report.issues:
        print(f"{issue.severity.value.upper()}: {issue.code}: {issue.message}")


if __name__ == "__main__":
    main()
