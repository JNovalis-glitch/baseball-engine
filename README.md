# Baseball Engine

A youth baseball lineup and roster-planning engine for the 7U Summer Travel program.

The engine is designed to turn the coaching program's source documents and roster workbook into a validated, coach-ready lineup card.

## Purpose

The Baseball Engine helps coaches build lineups that balance:

- player development
- competitive defensive alignment
- season-long fairness
- roster availability
- A/B/C player classification
- pitching and catching constraints
- printable Excel lineup-card output

The goal is not to create a perfect mathematical lineup in isolation. The goal is to produce a valid, explainable pre-game plan that follows the program rules and can be reviewed by coaches.

## Source Of Truth

The project is governed by the full document packet in the Project Library, summarized in:

- [`docs/SOURCE_OF_TRUTH.md`](docs/SOURCE_OF_TRUTH.md)

The source documents include:

- `7U Summer Travel (7).xlsx`
- `PLAYER RANKINGS & DEPTH CHART`
- `7U Summer Travel Baseball - Operating Rules`
- `LINEUP CONSTRUCTION PROCESS`
- `LINEUP TEMPLATE & EXAMPLES`
- `Program Management Guide`

The Excel roster workbook remains the operational source of truth for player status, rank, pitcher flag, coaches-kid flag, availability, games played, and season tracking.

## Lineup Construction Hierarchy

The engine follows the documented construction order:

1. Spreadsheet
2. Participation grid
3. Pitching and catching plan
4. Field-area rotation
5. Player assignment grid
6. Validation
7. Position grid
8. Coach review
9. Print

Positions are not assigned until the participation grid is built and validated.

## Core Game Rules

For a standard 7U game:

- 6 innings
- 12 players on the game roster
- 10 defensive positions per inning
- 2 bench players per inning
- every player sits exactly once whenever practical
- no consecutive bench innings
- coach-pitch innings: 1st, 2nd, 5th, 6th
- kid-pitch innings: 3rd and 4th

## Position Rules

- Only A players are eligible for 1B.
- A players are primary pitchers.
- A players are primary kid-pitch catchers.
- Strongest defenders generally play the left side of the field.
- Best outfielder should play LCF.
- A players anchor the defense and support developing players.
- Kid-pitch innings are useful opportunities for B/C player infield reps.

## Defensive Priorities

Coach-pitch innings prioritize:

1. 1B
2. SS
3. P
4. LCF
5. LF
6. 3B
7. 2B
8. RCF
9. RF
10. C

Kid-pitch innings prioritize:

1. P
2. C
3. developmental position opportunities

## Current Implementation Status

Implemented:

- project structure
- spreadsheet reader for the real 7U workbook shape
- domain models
- configurable rules
- structured validator
- explicit kid-pitch innings
- pitcher locks
- first-class participation grid
- Excel lineup-card output

Next major module:

- field-area rotation optimizer: IF / OF / Bench pattern planning before exact position assignment

## Validation Philosophy

Administrative accuracy comes before optimization.

A valid lineup is always better than a theoretically stronger lineup that contains assignment errors.

The validator checks for issues such as:

- wrong number of fielders
- wrong number of bench players
- duplicate assignments
- missing players
- ineligible 1B assignments
- pitching/catching rule violations
- bench fairness
- development opportunity warnings

## Output

The engine produces an Excel lineup card in the coach-facing format:

- positions down the left
- innings across the top
- bench rows at the bottom
- supporting roster and validation sheets

## Development Notes

Build one module at a time. Each milestone should be:

- documented
- unit tested
- validated against the source-of-truth rules
- committed with a meaningful message

Do not begin advanced lineup optimization until the validator and participation grid foundation are stable.
