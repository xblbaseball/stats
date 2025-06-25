In order to aggregate stats from game records, we need to convert spreadsheets that have evolved organically to a standardized data format for stats collection.

### A Standardized Game Record

The Pandas `DataFrame` we want should have the following columns.

| Column | Pandas Data Type |
| - | - |
| `season` |                    `int64` |
| `week` |             `string[python]` |
| `player` |             `string[python]` |
| `team` |             `string[python]` |
| `rs` |                      `float64` |
| `ra` |                      `float64` |
| `opponent` |         `string[python]` |
| `opponent_team` |         `string[python]` |
| `e` |                       `float64` |
| `innings` |                      `float64` |
| `innings_pitching` |                      `float64` |
| `innings_hitting` |                      `float64` |
| `ab` |                      `float64` |
| `h` |                       `float64` |
| `hr` |                      `float64` |
| `rbi` |                     `float64` |
| `bb` |                      `float64` |
| `so` |                      `float64` |
| `oppab` |                   `float64` |
| `opph` |                    `float64` |
| `opphr` |                   `float64` |
| `opprbi` |                  `float64` |
| `oppbb` |                   `float64` |
| `oppso` |                   `float64` |
| `league` |           `string[python]` |
| `game` |                      `int64` |
| `win` |                       `int64` |
| `loss` |                      `int64` |
| `run_rule_win` |              `int64` |
| `run_rule_loss` |             `int64` |
| `round` |                    `object` (will change) |
| `playoffs` |                   `bool` |

### Spreadsheet Columns (subject to LO change)

Currently, this is what the relevant spreadsheets mean and what columns they have. League names are always implied as spreadsheets are recorded per-league.

#### `Box Scores`

Scores from the current regular season that use team names, not player names.

Columns differ by league but generally look like so.

| Column | Type |
| - | - |
|`Week` | string |
|`Away` | string |
|`A. Score` | number |
|`H. Score` | number |
|`Home` | number |
|`A. E` | number |
|`H. E` | number |
|`IP` | number |
|`A. AB` | number |
|`A. R` | number |
|`A. H` | number |
|`A. HR` | number |
|`A. RBI` | number |
|`A. BB` | number |
|`A. SO` | number |
|`H. AB` | number |
|`H. R` | number |
|`H. H` | number |
|`H. HR` | number |
|`H. RBI` | number |
|`H. BB` | number |
|`H. SO` | number |

#### `Playoffs`

Scores from the current playoffs that use team names, not player names. The only difference between `Playoffs` and `Box Scores` is that `Week` is replaced with `Round`. `Round` is always prefixed with an `P` then either a number or a description of the playoff round.

| Column | Type |
| - | - |
|`Round` | string |
|`Away` | string |
|`A. Score` | number |
|`H. Score` | number |
|`Home` | number |
|`A. E` | number |
|`H. E` | number |
|`IP` | number |
|`A. AB` | number |
|`A. R` | number |
|`A. H` | number |
|`A. HR` | number |
|`A. RBI` | number |
|`A. BB` | number |
|`A. SO` | number |
|`H. AB` | number |
|`H. R` | number |
|`H. H` | number |
|`H. HR` | number |
|`H. RBI` | number |
|`H. BB` | number |
|`H. SO` | number |

#### `Head to Head`

Career season stats that persis across all seasons of XBL. When a season ends, regular season scores are copied to this spreadsheet and the team names are replaced with player names. Column names are slightly different as well.

The exact columns differ by league but generally look like so.

| Column | Type |
| - | - |
| `Season` | number |
| `Week` | string |
| `Away Player` | string |
| `Away Result` | `W` or `L` |
| `Away Score` | number |
| `Home Score` | number |
| `Home Result` | `W` or `L` |
| `Home Player` | string |
| `A E` | number |
| `H E` | number |
| `IP` | number |
| `A AB` | number |
| `A R` | number |
| `A H` | number |
| `A HR` | number |
| `A RBI` | number |
| `A BB` | number |
| `A SO` | number |
| `H AB` | number |
| `H R` | number |
| `H H` | number |
| `H HR` | number |
| `H RBI` | number |
| `H BB` | number |
| `H SO` | number |

When the spreadsheet is for playoff series, replace `Week` with `Round`, otherwise the stats are the same. Also note that, probably for aesthetic reason, the playoffs versions of `Head to Head` has empty columns.