import unittest

from game_plan import load_game_plan, parse_game_plan
from generator import generate_lineup
from models import Position, Tier


class GamePlanTest(unittest.TestCase):
    def test_parse_game_plan(self):
        plan = parse_game_plan({
            "players": [
                {"name": "Auggie", "tier": "A", "pitcher": True},
                {"name": "Dillon", "tier": "C", "new_player": True},
            ],
            "locks": [
                {"inning": 3, "position": "P", "player": "Auggie"},
            ],
            "preferences": {
                "top_defenders": ["Auggie"],
                "development_focus": ["Dillon"],
                "avoid_positions": [
                    {"player": "Dillon", "position": "P", "innings": [1]},
                ],
            },
        })

        self.assertEqual("Auggie", plan.players[0].name)
        self.assertEqual(Tier.C, plan.players[1].tier)
        self.assertTrue(plan.players[1].new_player)
        self.assertEqual(Position.P, plan.locks[0].position)
        self.assertEqual(("Auggie",), plan.preferences.top_defenders)
        self.assertEqual(("Dillon",), plan.preferences.development_focus)
        self.assertEqual(1, plan.preferences.avoid_positions[0].innings[0])

    def test_sample_game_plan_generates_valid_lineup(self):
        plan = load_game_plan("examples/july8_braves.json")
        generated = generate_lineup(plan.players, plan.locks, preferences=plan.preferences)

        self.assertTrue(generated.report.ok)


if __name__ == "__main__":
    unittest.main()
