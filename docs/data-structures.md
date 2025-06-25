We need to convert spreadsheets that have evolved organically to a standardized data format for stats collection.

### A Standardized Game Record

The Pandas `DataFrame` we want should have the following columns.

TODO Need to account for team names, player names.

| Column Name | Pandas data type |
| - | - |
| `season` |                    `int64` |
| `week` |             `string[python]` |
| `team` |             `string[python]` |
| `rs` |                      `float64` |
| `ra` |                      `float64` |
| `opponent` |         `string[python]` |
| `e` |                       `float64` |
| `ip` |                      `float64` |
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