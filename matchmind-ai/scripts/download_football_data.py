"""Download completed English top-flight seasons from Football-Data.co.uk.

Only result and match-stat columns are retained. Betting-odds columns are discarded.
Review the publisher's current usage terms before redistributing downloaded data.
"""
from pathlib import Path
from urllib.request import urlopen

import pandas as pd


# Season IDs to fetch, newest last.
SEASONS = ["2122", "2223", "2324", "2425", "2526"]
# Keep only the columns needed for this project.
KEEP = ["Date", "HomeTeam", "AwayTeam", "FTHG", "FTAG", "FTR", "HST", "AST"]


def main() -> None:
    """Download several CSV seasons and rewrite the bundled training dataset."""
    frames = []
    for season in SEASONS:
        # Load one season, keep the needed columns, and tag the source.
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
    # Combine all seasons into the repository's main dataset file.
    destination = Path(__file__).resolve().parents[1] / "backend" / "data" / "matches.csv"
    pd.concat(frames, ignore_index=True).to_csv(destination, index=False)
    print(f"Saved {destination}")


if __name__ == "__main__":
    main()
