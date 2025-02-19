import argparse
from dotenv import load_dotenv
import os
from pathlib import Path
import urllib.request

load_dotenv()


class SheetsNamespace(argparse.Namespace):
    save_dir: Path
    g_sheets_api_key: str


def arg_parser():
    parser = argparse.ArgumentParser(description="Save copies of Google Sheets data")
    parser.add_argument(
        "--save-dir",
        "-s",
        type=Path,
        default=Path("public/raw"),
        help="Path to save sheets data",
    )
    parser.add_argument(
        "--g-sheets-api-key",
        "-g",
        type=str,
        default=os.getenv("G_SHEETS_API_KEY", None),
        help="A Google Sheets API key. If this argument is not set, we'll look for a `G_SHEETS_API_KEY' env var",
    )

    return parser


LEAGUES = {
    "XBL": "1x5vwIVqk3-vEypu6dQb9Vb3kzVl9i2tA_zTcDK4I9LU",
    "AAA": "1Dq7fLYeqsvAbwljnzcyhNQ4s2bDeaZky1pQeSJQdAps",
    "AA": "14HmPir8MqsTyQE4BF3nxZVjsJL1MFACto4RDpH9eKqQ",
}

ALL_TIME_STATS = {
    "CAREER_STATS": "1wkLJTKO6Tk49if6L4iXJywWezOmseJjKKkCRvAKs7bg",
    "PLAYOFF_STATS": "1HWs44qhq9Buit3FIMfyh9j9G26hpnD7Eptv80FOntzg",
}


def collect_league_stats(json_dir: Path, g_sheets_api_key: str):
    tabs = ["Standings", "Hitting", "Pitching", "Playoffs", "Box%20Scores"]

    for league in LEAGUES:
        for tab in tabs:
            print(f"requesting {league} {tab}...", end="")
            url = f"https://sheets.googleapis.com/v4/spreadsheets/{LEAGUES[league]}/values/{tab}?key={g_sheets_api_key}"

            with urllib.request.urlopen(url) as req, open(
                json_dir.joinpath(f"{league}__{tab}.json"), "wb"
            ) as f:
                f.write(req.read())

            print(f" saved {league} {tab}")


def collect_all_time_stats(json_dir: Path, g_sheets_api_key: str):
    common_tab_suffixes = [
        ["Team", "Abbreviations"],
        ["Head", "to", "Head"],
        ["Standings", "Stats"],
        ["Hitting", "Stats"],
        ["Pitching", "Stats"],
        ["Career", "Stats"],
    ]

    tabs = [
        "%20".join([league] + tab)
        for tab in common_tab_suffixes
        for league in ["XBL", "AAA", "AA"]
    ]

    for sheet in ALL_TIME_STATS:
        for tab in tabs:
            print(f"requesting {sheet} {tab}...", end="")

            url = f"https://sheets.googleapis.com/v4/spreadsheets/{ALL_TIME_STATS[sheet]}/values/{tab}?key={g_sheets_api_key}"

            data = {}
            with urllib.request.urlopen(url) as req, open(
                json_dir.joinpath(f"{sheet}__{tab}.json"), "wb"
            ) as f:
                f.write(req.read())

            print(f" saved {sheet} {tab}")


def main(args: SheetsNamespace):
    if args.g_sheets_api_key is None or args.g_sheets_api_key == "":
        raise Exception("Missing Google Drive API key")

    # make sure the json dir exists
    args.save_dir.mkdir(parents=True, exist_ok=True)

    collect_league_stats(args.save_dir, args.g_sheets_api_key)
    collect_all_time_stats(args.save_dir, args.g_sheets_api_key)


if __name__ == "__main__":
    parser = arg_parser()
    args: SheetsNamespace = parser.parse_args()
    main(args)
