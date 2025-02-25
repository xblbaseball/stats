# XBL Stats

_Make sense of raw stats. Serve aggregated and processed stats at https://xblbaseball.github.io/stats._

## Usage

Hit the following URLs with your favorite HTTP client and JSON reader to get stats.

**Careers Data**

Stats for each player by league and all-time. Also includes head-to-head stats.

- JSON Data: [https://xblbaseball.github.io/stats/careers.json](https://xblbaseball.github.io/stats/careers.json)
- JSON Schema: [https://xblbaseball.github.io/stats/schemas/careers-schema.json](https://xblbaseball.github.io/stats/schemas/careers-schema.json)

**Season Data**

Stats from the current season by league.

- XBL Data: [https://xblbaseball.github.io/stats/XBL.json](https://xblbaseball.github.io/stats/XBL.json)
- AAA Data: [https://xblbaseball.github.io/stats/AAA.json](https://xblbaseball.github.io/stats/AAA.json)
- AA Data: [https://xblbaseball.github.io/stats/AA.json](https://xblbaseball.github.io/stats/AA.json)
- JSON Schema: [https://xblbaseball.github.io/stats/schemas/season-schema.json](https://xblbaseball.github.io/stats/schemas/season-schema.json)

## Development

**Python 3.10** is required.

1. (Recommended) create a `.env` file at the root of the repo with the following contents:
```
G_SHEETS_API_KEY=
```
2. (Suggested) create a virtual environment with [`venv`](https://docs.python.org/3/library/venv.html) first. Alternatively, `conda` would be fine.
3. Install dependencies:
```sh
pip install -r requirements.txt
```
4. Test:
```sh
python -m unittest discover tests/
```
5. Pull the latest from Google Sheets. If you have not created a `.env` file, you'll need to pass the Google Sheets API key to `get-sheets.py` using the `--g-sheets-api-key` flag.
```sh
python get-sheets.py
```
6. Parse raw data to aggregate season and career stats
```sh
python main.py --season 18 # or whatever season we're on
```
7. If you change any of the models in `models.py`, update the JSON schemas too
```sh
python models.py
```

### Deployments

Stats are served with Github Pages. We rebuild stats automatically twice a day (see the Github workflow).
