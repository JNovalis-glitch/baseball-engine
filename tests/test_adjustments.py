import unittest

from adjustments import PositionRequest, apply_position_requests
from generator import generate_lineup
from models import Position
from tests.test_generator import LOCKS, tonight_roster


class AdjustmentTest(unittest.TestCase):
    def test_position_request_noops_when_already_satisfied(self):
        generated = generate_lineup(tonight_roster(), LOCKS)

        result = apply_position_requests(
            generated.lineup,
            [PositionRequest("Dillon", Position.THIRD, 1)],
            roster=tonight_roster(),
            locks=LOCKS,
        )

        self.assertTrue(result.satisfied)
        self.assertEqual((), result.changes)

    def test_position_request_finds_valid_swap(self):
        generated = generate_lineup(tonight_roster(), LOCKS)

        result = apply_position_requests(
            generated.lineup,
            [PositionRequest("Dillon", Position.LF, 2)],
            roster=tonight_roster(),
            locks=LOCKS,
        )

        self.assertTrue(result.satisfied)
        self.assertTrue(result.report.ok)
        self.assertGreaterEqual(
            sum(1 for inning in result.lineup[Position.LF] if inning == ["Dillon"]),
            2,
        )
        self.assertTrue(result.changes)


if __name__ == "__main__":
    unittest.main()
