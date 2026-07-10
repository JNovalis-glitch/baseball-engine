import unittest

from explain import explain_lineup, format_explanation
from generator import generate_lineup
from models import Position
from tests.test_generator import LOCKS, tonight_roster


class ExplainTest(unittest.TestCase):
    def test_explanation_includes_validation_and_locks(self):
        roster = tonight_roster()
        generated = generate_lineup(roster, LOCKS)

        explanation = explain_lineup(generated.lineup, roster, generated.report, LOCKS)
        text = format_explanation(explanation)

        self.assertIn("Hard validation passes.", text)
        self.assertIn("Lock honored: James at P in the 3rd.", text)
        self.assertIn("Lock honored: Connor at C in the 4th.", text)
        self.assertIn("Player paths:", text)

    def test_player_summary_tracks_bench_and_outfield(self):
        roster = tonight_roster()
        generated = generate_lineup(roster, LOCKS)
        explanation = explain_lineup(generated.lineup, roster, generated.report, LOCKS)
        summaries = {summary.player_name: summary for summary in explanation.player_summaries}

        self.assertEqual((2,), summaries["Bobby"].bench_innings)
        self.assertTrue(all(isinstance(inning, int) for inning in summaries["Dillon"].outfield_innings))
        self.assertEqual(Position.BENCH.value, summaries["Teddy"].positions[5])


if __name__ == "__main__":
    unittest.main()
