import unittest

from generator import generate_lineup
from models import Player, Position, Tier
from preferences import CoachPreferences, PositionAvoidance
from validator import PositionLock


def tonight_roster():
    return [
        Player("Auggie", Tier.A, pitcher=True, catcher=True),
        Player("Bobby", Tier.B, catcher=True),
        Player("Connor", Tier.A, pitcher=True, catcher=True),
        Player("Dillon", Tier.C),
        Player("James", Tier.A, pitcher=True, catcher=True),
        Player("Killian", Tier.B, catcher=True),
        Player("Remy", Tier.B, pitcher=True, catcher=True),
        Player("River", Tier.B),
        Player("Miles", Tier.B),
        Player("Teddy", Tier.A, pitcher=True),
        Player("Wesley", Tier.C, catcher=True),
        Player("Weston", Tier.A, pitcher=True),
    ]


LOCKS = [
    PositionLock(3, Position.P, "James"),
    PositionLock(3, Position.C, "Auggie"),
    PositionLock(4, Position.P, "Teddy"),
    PositionLock(4, Position.C, "Connor"),
]


class GeneratorTest(unittest.TestCase):
    def test_generator_produces_valid_lineup(self):
        generated = generate_lineup(tonight_roster(), LOCKS)

        self.assertTrue(generated.report.ok)
        self.assertEqual([], list(generated.report.errors))

    def test_generator_honors_pitcher_and_catcher_locks(self):
        generated = generate_lineup(tonight_roster(), LOCKS)
        lineup = generated.lineup

        self.assertEqual(["James"], lineup[Position.P][2])
        self.assertEqual(["Auggie"], lineup[Position.C][2])
        self.assertEqual(["Teddy"], lineup[Position.P][3])
        self.assertEqual(["Connor"], lineup[Position.C][3])

    def test_generator_respects_position_avoidance(self):
        preferences = CoachPreferences(
            avoid_positions=(
                PositionAvoidance("Auggie", Position.P, (1,)),
            )
        )

        generated = generate_lineup(tonight_roster(), LOCKS, preferences=preferences)

        self.assertTrue(generated.report.ok)
        self.assertNotEqual(["Auggie"], generated.lineup[Position.P][0])

    def test_top_defenders_are_spread_in_first_inning_infield(self):
        preferences = CoachPreferences(
            top_defenders=("Auggie", "Connor", "James", "Teddy", "Weston"),
            spread_first_inning_infield_strength=True,
        )

        generated = generate_lineup(tonight_roster(), LOCKS, preferences=preferences)
        first_inning_second = generated.lineup[Position.SECOND][0][0]
        first_inning_third = generated.lineup[Position.THIRD][0][0]

        self.assertNotIn(first_inning_second, preferences.top_defenders)
        self.assertNotIn(first_inning_third, preferences.top_defenders)


if __name__ == "__main__":
    unittest.main()
