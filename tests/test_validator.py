import unittest
from pathlib import Path

from lineup_io import parse_tsv_lineup
from models import Position
from validator import PositionLock, validate_lineup


VALID_CARD = """Position	1st	2nd	3rd	4th	5th	6th
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


class ValidatorTest(unittest.TestCase):
    def test_parser_accepts_utf8_bom(self):
        lineup = parse_tsv_lineup("\ufeff" + VALID_CARD)
        report = validate_lineup(lineup, locks=LOCKS)

        self.assertTrue(report.ok)

    def test_valid_card_passes_hard_checks(self):
        report = validate_lineup(parse_tsv_lineup(VALID_CARD), locks=LOCKS)

        self.assertTrue(report.ok)
        self.assertEqual([], list(report.errors))

    def test_hand_tweaked_card_passes_hard_checks(self):
        text = Path("examples/july8_hand_tweaked.tsv").read_text(encoding="utf-8")
        report = validate_lineup(parse_tsv_lineup(text), locks=LOCKS)

        self.assertTrue(report.ok)
        self.assertEqual([], list(report.errors))

    def test_duplicate_player_is_an_error(self):
        bad_card = VALID_CARD.replace("RCF\tRiver", "RCF\tWeston", 1)

        report = validate_lineup(parse_tsv_lineup(bad_card), locks=LOCKS)
        codes = {issue.code for issue in report.errors}

        self.assertIn("duplicate_player", codes)
        self.assertIn("missing_player", codes)

    def test_broken_pitcher_lock_is_an_error(self):
        bad_card = VALID_CARD.replace("P\tConnor\tRemy\tJames", "P\tConnor\tRemy\tTeddy", 1)

        report = validate_lineup(parse_tsv_lineup(bad_card), locks=LOCKS)
        codes = {issue.code for issue in report.errors}

        self.assertIn("lock_broken", codes)

    def test_consecutive_outfield_is_an_error(self):
        bad_card = VALID_CARD.replace("RCF\tRiver\tWesley", "RCF\tRiver\tDillon", 1)
        bad_card = bad_card.replace("Bench\tRemy\tDillon", "Bench\tRemy\tWesley", 1)

        report = validate_lineup(parse_tsv_lineup(bad_card), locks=LOCKS)
        codes = {issue.code for issue in report.errors}

        self.assertIn("consecutive_outfield", codes)


if __name__ == "__main__":
    unittest.main()
