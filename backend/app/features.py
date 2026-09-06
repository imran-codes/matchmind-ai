from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import dataclass, field
from typing import Any

import pandas as pd


FEATURES = [
    # These are the numbers the model sees for each fixture.
    "home_form_points",
    "away_form_points",
    "home_goals_for",
    "away_goals_for",
    "home_goals_against",
    "away_goals_against",
    "home_shots_on_target",
    "away_shots_on_target",
    "form_edge",
    "attack_edge",
    "defence_edge",
    "home_elo",
    "away_elo",
    "elo_edge",
]


@dataclass
class TeamState:
    matches: deque[dict[str, float]] = field(default_factory=lambda: deque(maxlen=5))
    elo: float = 1500.0

    def summary(self) -> dict[str, float]:
        # Summarize the last five matches into a lightweight pre-match profile.
        if not self.matches:
            return {"points": 1.0, "gf": 1.2, "ga": 1.2, "sot": 4.0, "elo": self.elo}
        count = len(self.matches)
        return {"elo": self.elo, **{
            key: sum(match[key] for match in self.matches) / count
            for key in ("points", "gf", "ga", "sot")
        }}


def feature_vector(home: dict[str, float], away: dict[str, float]) -> dict[str, float]:
    # Convert two team summaries into the model inputs used for a single fixture.
    return {
        "home_form_points": home["points"],
        "away_form_points": away["points"],
        "home_goals_for": home["gf"],
        "away_goals_for": away["gf"],
        "home_goals_against": home["ga"],
        "away_goals_against": away["ga"],
        "home_shots_on_target": home["sot"],
        "away_shots_on_target": away["sot"],
        "form_edge": home["points"] - away["points"],
        "attack_edge": home["gf"] - away["ga"],
        "defence_edge": away["gf"] - home["ga"],
        "home_elo": home["elo"],
        "away_elo": away["elo"],
        "elo_edge": home["elo"] - away["elo"],
    }


def build_training_frame(
    matches: pd.DataFrame, window: int = 5
) -> tuple[pd.DataFrame, dict[str, dict[str, float]]]:
    """Build pre-match features chronologically; the current result is never a feature."""
    # Validate the raw dataset before any feature engineering starts.
    required = {"Date", "HomeTeam", "AwayTeam", "FTHG", "FTAG", "FTR", "HST", "AST"}
    missing = required.difference(matches.columns)
    if missing:
        raise ValueError(f"Missing columns: {sorted(missing)}")

    if window != 5:
        raise ValueError("This release supports a five-match window only")
    frame = matches.copy()
    frame["Date"] = pd.to_datetime(frame["Date"], dayfirst=True, errors="coerce")
    for column in ("FTHG", "FTAG", "HST", "AST"):
        frame[column] = pd.to_numeric(frame[column], errors="coerce")
        if ((frame[column] < 0) | (frame[column] % 1 != 0)).any():
            raise ValueError(f"Invalid nonnegative integer statistic: {column}")
    if frame[list(required)].isna().any().any():
        raise ValueError("Missing/invalid data: ingestion must resolve it before training")
    expected = frame.apply(lambda row: "H" if row.FTHG > row.FTAG else "A" if row.FTHG < row.FTAG else "D", axis=1)
    if not (frame.FTR == expected).all():
        raise ValueError("Result labels disagree with scores")
    if (frame.HomeTeam == frame.AwayTeam).any() or frame.duplicated(["Date", "HomeTeam", "AwayTeam"]).any():
        raise ValueError("Invalid or duplicated fixture")
    frame = frame.sort_values("Date", kind="stable")
    states: dict[str, TeamState] = defaultdict(TeamState)
    rows: list[dict[str, Any]] = []

    # Build features before updating state so each row only sees earlier matches.
    # Without kick-off times, never use another result from the same date.
    for _, day in frame.groupby("Date", sort=True):
        for match in day.itertuples(index=False):
            home_state = states[match.HomeTeam]
            away_state = states[match.AwayTeam]
            if len(home_state.matches) >= window and len(away_state.matches) >= window:
                rows.append(
                    {
                        "Date": match.Date,
                        "HomeTeam": match.HomeTeam,
                        "AwayTeam": match.AwayTeam,
                        **feature_vector(home_state.summary(), away_state.summary()),
                        "label": match.FTR,
                    }
                )
        for match in day.itertuples(index=False):
            # Now that the day has been scored, roll the observed result into each team state.
            home_state, away_state = states[match.HomeTeam], states[match.AwayTeam]
            home_points = 3.0 if match.FTR == "H" else 1.0 if match.FTR == "D" else 0.0
            away_points = 3.0 if match.FTR == "A" else 1.0 if match.FTR == "D" else 0.0
            expected_home = 1 / (1 + 10 ** ((away_state.elo - home_state.elo - 60) / 400))
            actual_home = 1.0 if match.FTR == "H" else .5 if match.FTR == "D" else 0.0
            change = 20 * (actual_home - expected_home)
            home_state.elo += change
            away_state.elo -= change
            home_state.matches.append(
                {"points": home_points, "gf": float(match.FTHG), "ga": float(match.FTAG), "sot": float(match.HST)}
            )
            away_state.matches.append(
                {"points": away_points, "gf": float(match.FTAG), "ga": float(match.FTHG), "sot": float(match.AST)}
            )
    # Keep only teams with enough history to produce stable five-match profiles.
    profiles = {team: state.summary() for team, state in sorted(states.items()) if len(state.matches) == 5}
    return pd.DataFrame(rows), profiles
