from explain import explain_lineup, format_explanation
from generator import generate_lineup
from lineup_io import format_tsv_lineup
from models import Player, Position, Tier
from preferences import CoachPreferences
from validator import PositionLock


ROSTER = [
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


PREFERENCES = CoachPreferences(
    top_defenders=("Auggie", "Connor", "James", "Teddy", "Weston"),
    development_focus=("Dillon", "Wesley"),
)


def main() -> None:
    generated = generate_lineup(ROSTER, LOCKS, preferences=PREFERENCES)
    explanation = explain_lineup(generated.lineup, ROSTER, generated.report, LOCKS)

    print(format_tsv_lineup(generated.lineup))
    print()
    print(format_explanation(explanation))


if __name__ == "__main__":
    main()
