import pandas as pd

from app.features import build_training_frame


def test_features_are_created_only_after_prior_history() -> None:
    rows = []
    for index in range(12):
        rows.append({"Date": f"{index + 1:02d}/01/2025", "HomeTeam": "A" if index % 2 == 0 else "B", "AwayTeam": "B" if index % 2 == 0 else "A", "FTHG": 1, "FTAG": 0, "FTR": "H", "HST": 4, "AST": 2})
    frame, _ = build_training_frame(pd.DataFrame(rows), window=5)
    assert len(frame) == 7
    assert frame.iloc[0]["Date"] == pd.Timestamp("2025-01-06")


def test_current_result_cannot_change_its_own_features():
    from app.features import FEATURES
    rows = [{"Date": f"{i+1:02d}/01/2025", "HomeTeam": "A", "AwayTeam": "B", "FTHG":1,
             "FTAG":0, "FTR":"H", "HST":4, "AST":2} for i in range(12)]
    before, _ = build_training_frame(pd.DataFrame(rows))
    rows[6].update(FTHG=0, FTAG=5, FTR="A", HST=0, AST=10)
    after, _ = build_training_frame(pd.DataFrame(rows))
    assert before.loc[1, FEATURES].equals(after.loc[1, FEATURES])
    assert not before.loc[2, FEATURES].equals(after.loc[2, FEATURES])


def test_matches_on_same_date_cannot_see_each_others_results():
    from app.features import FEATURES
    rows = [{"Date": f"{i+1:02d}/01/2025", "HomeTeam": "A", "AwayTeam": "B", "FTHG":1,
             "FTAG":0, "FTR":"H", "HST":4, "AST":2} for i in range(8)]
    rows.append({"Date":"08/01/2025", "HomeTeam":"B", "AwayTeam":"A", "FTHG":1,
                 "FTAG":0, "FTR":"H", "HST":4, "AST":2})
    before, _ = build_training_frame(pd.DataFrame(rows))
    rows[7].update(FTHG=0, FTAG=5, FTR="A", HST=0, AST=10)
    after, _ = build_training_frame(pd.DataFrame(rows))
    assert before.iloc[-1][FEATURES].equals(after.iloc[-1][FEATURES])
