"""Small real-provider behavioural smoke suite via the running application.

Run against the local API or authenticated Cloud Run proxy. Calls can incur Vertex costs.
This is deliberately separate from the mocked, repeatable unit/contract tests.
"""
import argparse
import json
import math
import sys
import time
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

CASES = [
    ("explicit_fixture", "Predict Arsenal at home against Liverpool", [("Arsenal", "Liverpool")]),
    ("two_fixtures", "Predict Arsenal at home against Liverpool and Chelsea at home against Man City", [("Arsenal", "Liverpool"), ("Chelsea", "Man City")]),
    ("incomplete_fixture", "Predict Arsenal's next match", []),
    ("unknown_teams", "Predict Imaginary Purple FC against Invented Orange FC. Do not substitute other teams.", []),
]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default="http://localhost:8000")
    parser.add_argument("--output", default="evals/live-report.json")
    args = parser.parse_args()
    rows = []
    for name, message, expected in CASES:
        start = time.perf_counter()
        try:
            request = Request(args.url.rstrip("/") + "/api/analyse",
                              data=json.dumps({"message": message}).encode(),
                              headers={"Content-Type": "application/json"})
            with urlopen(request, timeout=75) as response:
                data = json.load(response)
            observed = [(p["home_team"], p["away_team"]) for p in data["predictions"]]
            valid = all(all(math.isfinite(v) and 0 <= v <= 1 for v in p["probabilities"].values())
                        and abs(sum(p["probabilities"].values())-1) < 1e-5 for p in data["predictions"])
            passed = sorted(observed) == sorted(expected) and valid and data["status"] != "partial"
            rows.append({"case": name, "passed": passed, "expected": expected, "observed": observed,
                         "status": data["status"], "request_id": data["request_id"],
                         "tool_calls": data["tool_calls"], "seconds": round(time.perf_counter()-start, 2)})
        except (HTTPError, OSError, ValueError, KeyError) as error:
            rows.append({"case": name, "passed": False, "error_type": type(error).__name__})
    report = {"cases": rows, "passed": sum(row["passed"] for row in rows), "total": len(rows),
              "scope": "Small live smoke suite. Does not establish accuracy, fairness or production safety."}
    destination = Path(args.output)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))
    sys.exit(0 if report["passed"] == report["total"] else 1)


if __name__ == "__main__":
    main()
