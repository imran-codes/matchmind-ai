"""Download completed English top-flight seasons from Football-Data.co.uk.

Only result and match-stat columns are retained. Betting-odds columns are discarded.
Review the publisher's current usage terms before redistributing downloaded data.
"""
from pathlib import Path
from urllib.request import urlopen

import pandas as pd


SEASONS = ["2122", "2223", "2324", "2425", "2526"]
KEEP = ["Date", "HomeTeam", "AwayTeam", "FTHG", "FTAG", "FTR", "HST", "AST"]


def main() -> None:
    frames = []
    for season in SEASONS:
        url = f"https://www.football-data.co.uk/mmz4281/{season}/E0.csv"
        with urlopen(url, timeout=20) as response:
            frame = pd.read_csv(response)
        missing = set(KEEP).difference(frame.columns)
        if missing:
            raise RuntimeError(f"{season} is missing {sorted(missing)}")
        frame = frame[KEEP].copy()
        frame["season"] = season
        frame["data_origin"] = "football-data.co.uk"
        frames.append(frame)
        print(f"Downloaded {season}: {len(frame)} matches")
    destination = Path(__file__).resolve().parents[1] / "backend" / "data" / "matches.csv"
    pd.concat(frames, ignore_index=True).to_csv(destination, index=False)
    print(f"Saved {destination}")


if __name__ == "__main__":
    main()
