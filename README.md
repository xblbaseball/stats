# XBL Stats

_Make sense of raw stats. Serve aggregated and processed stats at https://xblbaseball.github.io/stats._

## Usage

Hit the following URLs with your favorite HTTP client and JSON reader to get stats.

**Careers Data**

Stats for each player by league and all-time. Also includes head-to-head stats.

- JSON Data: [https://xblbaseball.github.io/stats/careers.json]()
- JSON Schema: [https://xblbaseball.github.io/stats/schemas/career-schema.json]()

**Season Data**

Stats from the current season by league.

- XBL Data: [https://xblbaseball.github.io/stats/XBL.json]()
- AAA Data: [https://xblbaseball.github.io/stats/AAA.json]()
- AA Data: [https://xblbaseball.github.io/stats/AA.json]()
- JSON Schema: [https://xblbaseball.github.io/stats/schemas/season-schema.json]()

## Development

* Python 3.10

Test with

```sh
python -m unittest discover tests/
```

Collect and parse stats with

```sh
python get-sheets.py
python main.py --season 18
```

If you change any of the models in `models.py`, update the equivalent TS types by doing the following:

```sh
# save JSON schemas from the models
python models.py
```
