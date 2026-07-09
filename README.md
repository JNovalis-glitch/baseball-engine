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
- Development players should get varied looks when practical: avoid repeating
  the same outfield spot and prefer a corner outfield plus infield mix, including
  3B reps where the lineup remains valid.

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
- repeated same-position development patterns

## Output

The engine produces an Excel lineup card in the coach-facing format:

- positions down the left
- innings across the top
- bench rows at the bottom
- supporting roster and validation sheets

## Game Plan JSON

Lineups can be generated from a small game-plan file:

```bash
python -m cli generate examples/july8_braves.json
```

The JSON contains:

- `players`: roster entries with `name`, `tier`, `pitcher`, `catcher`,
  `new_player`, and `active`
- `locks`: exact assignments such as James pitching the 3rd and Auggie catching
- `preferences`: coaching intent such as top defenders, development-focus
  players, avoided positions, and first-inning strength spreading

Example preference fields:

```json
{
  "top_defenders": ["Auggie", "Connor", "James"],
  "development_focus": ["Dillon"],
  "spread_first_inning_infield_strength": true,
  "avoid_positions": [
    {"player": "Blake", "position": "P", "innings": [1]}
  ]
}
```

Small coach-requested swaps can be searched from an existing TSV lineup:

```bash
python -m cli adjust examples/generated_july8.tsv \
  --game-plan examples/july8_braves.json \
  --request Dillon:3B:1
```

The adjust command only returns changes that still pass hard validation.

## Manual Tweak Workflow

The intended coach workflow is:

1. Generate an initial lineup.
2. Copy it into Sheets.
3. Make coach adjustments by hand.
4. Paste or save the adjusted TSV back into the engine.
5. Run validation before using the card.

Validate a saved TSV:

```bash
python -m cli validate examples/july8_hand_tweaked.tsv \
  --game-plan examples/july8_braves.json
```

Validate pasted TSV from stdin:

```bash
python -m cli validate - --game-plan examples/july8_braves.json
```

The validator reports hard errors separately from softer warnings, so duplicate
players, missing players, broken locks, bench mistakes, and back-to-back
outfield are easy to spot after manual edits.

## Development Notes

Build one module at a time. Each milestone should be:

- documented
- unit tested
- validated against the source-of-truth rules
- committed with a meaningful message

Do not begin advanced lineup optimization until the validator and participation grid foundation are stable.
