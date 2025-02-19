# XBL Stats

_Make sense of raw stats. Serve aggregated and processed stats at https://xblbaseball.github.io/stats._

## Usage

Hit the following URLs with your favorite HTTP client and JSON reader to get stats.

**Careers Data**

Stats for each player by league and all-time. Also includes head-to-head stats.

- JSON Data: [https://xblbaseball.github.io/stats/careers.json](https://xblbaseball.github.io/stats/careers.json)
- JSON Schema: [https://xblbaseball.github.io/stats/schemas/career-schema.json](https://xblbaseball.github.io/stats/schemas/career-schema.json)

**Season Data**

Stats from the current season by league.

- XBL Data: [https://xblbaseball.github.io/stats/XBL.json](https://xblbaseball.github.io/stats/XBL.json)
- AAA Data: [https://xblbaseball.github.io/stats/AAA.json](https://xblbaseball.github.io/stats/AAA.json)
- AA Data: [https://xblbaseball.github.io/stats/AA.json](https://xblbaseball.github.io/stats/AA.json)
- JSON Schema: [https://xblbaseball.github.io/stats/schemas/season-schema.json](https://xblbaseball.github.io/stats/schemas/season-schema.json)

## Development

**Python 3.10** is required.

(Suggested) create a virtual environment with `venv` first: [link](https://docs.python.org/3/library/venv.html). Alternatively, `conda` would be fine.

Install dependencies:

```sh
pip install -r requirements.txt
```

Test:

```sh
python -m unittest discover tests/
```

Pull the latest from Google Sheets:

```sh
python get-sheets.py
```

Parse raw data to aggregate season and career stats

```sh
python main.py --season 18 # or whatever season we're on
```

If you change any of the models in `models.py`, update the JSON schemas too

```sh
# save JSON schemas from the models
python models.py
```

### Deployments

Stats are served with Github Pages. We rebuild stats automatically twice a day (see the Github workflow).
