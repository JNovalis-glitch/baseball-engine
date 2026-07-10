import json
import unittest

from game_plan_builder import build_game_plan_json, parse_roster_text
from models import Tier


class GamePlanBuilderTest(unittest.TestCase):
    def test_parse_roster_text_supports_aliases_and_flags(self):
        players = parse_roster_text(
            "Theodore Smith | Theo | A | pitcher\n"
            "Maxwell Messner | Max | B | pitcher catcher\n"
            "Dillon Bartucci | Dillon | C\n"
        )

        self.assertEqual("Theo", players[0].card_name)
        self.assertEqual(Tier.A, players[0].tier)
        self.assertTrue(players[0].pitcher)
        self.assertEqual("Max", players[1].card_name)
        self.assertTrue(players[1].catcher)
        self.assertEqual(Tier.C, players[2].tier)

    def test_build_game_plan_json_adds_locks_and_preferences(self):
        data = json.loads(build_game_plan_json(
            "Auggie Novalis | Auggie | A | pitcher catcher\n"
            "James Cecchetelli | James | A | catcher\n",
            pitcher_locks=("Auggie:4",),
            catcher_locks=("James:4",),
            top_defenders=("Auggie", "James"),
            development_focus=("James",),
            avoid_positions=("James:RF:1",),
        ))

        self.assertEqual("Auggie", data["players"][0]["name"])
        self.assertTrue(data["players"][0]["pitcher"])
        self.assertEqual({"inning": 4, "position": "P", "player": "Auggie"}, data["locks"][0])
        self.assertEqual(["Auggie", "James"], data["preferences"]["top_defenders"])
        self.assertEqual({"player": "James", "position": "RF", "innings": [1]}, data["preferences"]["avoid_positions"][0])


if __name__ == "__main__":
    unittest.main()
