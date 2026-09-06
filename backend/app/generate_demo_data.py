"""Generate the synthetic fixture dataset used by the demo."""
from __future__ import annotations

from itertools import combinations
from pathlib import Path

import numpy as np
import pandas as pd


# Relative team strengths used to make the synthetic results look realistic.
TEAMS = {
    "Arsenal": 1.24,
    "Aston Villa": 1.06,
    "Bournemouth": 0.93,
    "Brentford": 0.96,
    "Brighton": 1.01,
    "Chelsea": 1.12,
    "Crystal Palace": 0.98,
    "Everton": 0.91,
    "Fulham": 0.97,
    "Leeds": 0.86,
    "Liverpool": 1.28,
    "Man City": 1.30,
    "Man United": 1.03,
    "Newcastle": 1.10,
    "Nott'm Forest": 0.95,
    "Sunderland": 0.82,
    "Tottenham": 1.04,
    "West Ham": 0.94,
    "Wolves": 0.88,
    "Burnley": 0.80,
}


def generate(output: Path, seasons: int = 5) -> Path:
    """Create a repeatable synthetic CSV of fixtures and match results."""
    rng = np.random.default_rng(42)
    rows: list[dict[str, object]] = []
    pairs = list(combinations(TEAMS, 2))
    start = pd.Timestamp("2021-08-01")

    for season in range(seasons):
        # Build a shuffled home/away round robin for each synthetic season.
        fixtures = [(a, b) for a, b in pairs] + [(b, a) for a, b in pairs]
        rng.shuffle(fixtures)
        for index, (home, away) in enumerate(fixtures):
            # Sample goals and shots from simple team-strength-based distributions.
            date = start + pd.Timedelta(days=season * 365 + index * 270 / len(fixtures))
            home_rate = 1.36 * TEAMS[home] / TEAMS[away]
            away_rate = 1.05 * TEAMS[away] / TEAMS[home]
            home_goals = int(rng.poisson(home_rate))
            away_goals = int(rng.poisson(away_rate))
            result = "H" if home_goals > away_goals else "A" if away_goals > home_goals else "D"
            home_sot = max(home_goals, int(rng.poisson(3.4 * TEAMS[home]) + home_goals))
            away_sot = max(away_goals, int(rng.poisson(3.1 * TEAMS[away]) + away_goals))
            rows.append(
                {
                    "Date": date.strftime("%d/%m/%Y"),
                    "HomeTeam": home,
                    "AwayTeam": away,
                    "FTHG": home_goals,
                    "FTAG": away_goals,
                    "FTR": result,
                    "HST": home_sot,
                    "AST": away_sot,
                    "data_origin": "synthetic_demo",
                }
            )

    output.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(output, index=False)
    return output


if __name__ == "__main__":
    # Regenerate the default dataset file when the module is run directly.
    destination = Path(__file__).resolve().parents[1] / "data" / "matches.csv"
    print(generate(destination))
