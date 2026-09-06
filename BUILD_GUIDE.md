# Build MatchMind from the beginning

Goal: explain and demonstrate an ADK agent that calls a real ML model. Budget roughly a
weekend for the local app, tests and first deployment. The lifecycle extensions can fill
the remaining days of your one-week limit; banking-grade operational approval is outside
that timebox. All commands here run from the extracted `matchmind-ai` folder unless stated.

## 1. Understand the three different pieces

| Piece | Responsibility | File |
|---|---|---|
| Gemini | Understand the question and choose tool arguments | Configured by GEMINI_MODEL |
| ADK | Describe tools, run the conversation and coordinate tool execution | backend/app/agent.py and agent_runtime.py |
| Classifier | Calculate home/draw/away probabilities from saved statistical features | backend/app/prediction.py |

An agent does not train the classifier. Training is a separate Python process. The UI
always takes its probability bars from the tool result, not from a number generated in prose.

## 2. Install and verify the tools

Use Python **3.12** for the same environment as the Docker image, Node **22.12 or newer**,
and the Google Cloud CLI (which includes `bq`). Docker Desktop is optional for local container testing.

```bash
python3.12 --version
node --version
gcloud --version
```

Open the extracted folder in PyCharm or VS Code. Set the interpreter to `.venv/bin/python`
after creating the environment below.

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r backend/requirements.lock
python -m pip check
```

`requirements.txt` lists the direct dependencies; `requirements.lock` records the complete
tested dependency set. Use the lock for this tutorial. Regenerate and re-test deliberately
when upgrading ADK or scikit-learn; do not independently upgrade the deployed runtime.

## 3. Inspect the data

The package contains 1,900 synthetic matches. Team strengths and fixture ordering are invented,
not historical claims about the clubs. It includes no odds, customers or player medical data.

```bash
python - <<'PY'
import pandas as pd
d = pd.read_csv('backend/data/matches.csv')
print(d.shape)
print(d.head(3).to_string(index=False))
print(d.FTR.value_counts(normalize=True))
PY
```

`FTR` is the label: H = home win, D = draw, A = away win. `HST` and `AST` are home/away
shots on target. Current-match statistics must never be used to predict that same match.

To regenerate the bundled dataset:

```bash
PYTHONPATH=backend python -m app.generate_demo_data
```

For a later experiment, `python scripts/download_football_data.py` replaces the CSV with
public football-data.co.uk match results. Read the source terms, inspect missing values
and rerun training. Club coverage and feature freshness will change. The release check
fails on missing/invalid data rather than silently training on broken rows. Download to a
separate working copy if you want to retain the synthetic demonstration unchanged.

## 4. Build features and train the model

Read `backend/app/features.py`. For each date it first creates feature rows using earlier
dates, then updates the histories after those rows are created. Matches on the same date
cannot leak into each other's inputs because kick-off times are unavailable.

Features include five-match form, goals for/against, shots on target and Elo ratings.
An Elo rating is a running estimate of team strength updated after results; it provides
longer-term context than five-match form. The Elo constants are tutorial assumptions.

```bash
PYTHONPATH=backend python -m app.train
```

The script uses chronological date boundaries: approximately 70% training, 15% validation
and 15% testing. It compares a class-prior baseline, logistic regression and gradient boosting.
The baseline simply repeats training outcome frequencies; it can legitimately win if the
features do not improve probability quality. Select by validation log loss, then report test
metrics. Do not repeatedly tune against the same test period and still call it untouched.

```bash
python -m json.tool backend/artifacts/metadata.json
```

Outputs:

- `model.joblib`: the selected estimator and preprocessing pipeline.
- `profiles.json`: the final five-match profiles and Elo ratings used for future fixture demos.
- `metadata.json`: candidate ranking, test metrics, cut-off date, versions and checksums.

Lower log loss and Brier score are better. Accuracy only checks the largest probability.
Inspect the selected model: a prior baseline gives the same probabilities for every fixture.
Saved profiles include the whole dataset, while historical evaluation uses rolling pre-match
profiles. The UI estimates hypothetical fixtures after the displayed cut-off; it cannot
reconstruct historical predictions or confirm a fixture is scheduled.

## 5. Create the agent — the main lesson for your video

Open `backend/app/agent.py`. Work through it in this order:

1. `INSTRUCTION`: the task, domain limits, ambiguity handling and response style.
2. `ToolState`: a per-request record of actual tool calls and prediction results.
3. `list_teams()`: a read-only Python function exposing supported names.
4. `predict_match(home_team, away_team)`: validates arguments and invokes the classifier.
5. `Agent(...)`: connects Gemini, the instructions and the allowed Python functions.

The core pattern is:

```python
return Agent(
    name='football_analyst',
    model=model,
    instruction=INSTRUCTION,
    tools=[list_teams, predict_match],
    generate_content_config=types.GenerateContentConfig(
        temperature=0,
        max_output_tokens=900,
    ),
)
```

ADK converts the functions' names, docstrings and type hints into tool declarations. Gemini
can request a tool call; Python then validates and executes it. Supplying a function to an
agent does not give it permission to run arbitrary Python, read files or browse the web.

This project has one agent with two tools. Sub-agents would add complexity without a separate
specialist job to perform. Explain that as an architectural choice, not a missing feature.

## 6. Configure Google Cloud for local ADK calls

Create or choose your personal learning project, enable billing and verify you have permission
to use Vertex AI. In Model Garden choose a currently available Gemini text model that supports
tool calling. Copy its exact model ID; availability and access can vary by project and location.

```bash
cp .env.example gcp.env
```

Edit `gcp.env`: set project ID, a globally unique bucket name, release label and GEMINI_MODEL.
Then load the values:

```bash
set -a
source gcp.env
set +a
export GOOGLE_CLOUD_PROJECT="$GCP_PROJECT"
gcloud auth login
gcloud config set project "$GCP_PROJECT"
gcloud services enable aiplatform.googleapis.com
gcloud auth application-default login
gcloud auth application-default set-quota-project "$GCP_PROJECT"
```

`gcloud auth login` authenticates CLI operations. Application Default Credentials (ADC)
authenticate the Python SDK locally. On Cloud Run, the runtime service account supplies
credentials automatically. Never commit ADC JSON or copy it into a container.

The example uses the global Gemini endpoint for a personal synthetic-data demo. That does
not promise UK data residency. For restricted data, select a supported approved region and
review service-specific processing guarantees.

## 7. Run the ADK development interface

From the repository root, with the environment loaded:

```bash
PYTHONPATH=backend adk web backend/agents --port 8001
```

Open http://localhost:8001 and select `football_agent`. Ask:

> Predict Arsenal at home against Liverpool. Explain the limitations.

Inspect the function-call and function-response events. You should see `predict_match`
with two team names, followed by the classifier's structured probabilities.

This UI is for one local developer. Its entrypoint resets demonstration tool state between
turns. It is not our production API and should not be exposed publicly. The main app creates
a separate agent and session for every request.

If Vertex returns 403, check API enablement and the caller's Vertex AI User permission. For
404, verify model ID and location. For 429, check quota and reduce requests. Errors are not
replaced with pretend agent answers.

## 8. Understand the API runner

Read `backend/app/agent_runtime.py`. It creates a session, constructs an ADK Runner and calls:

```python
runner.run_async(
    user_id=request_id,
    session_id=session.id,
    new_message=types.Content(role='user', parts=[types.Part(text=message)]),
    run_config=RunConfig(max_llm_calls=4),
)
```

The surrounding code applies a 60-second deadline, closes the event stream and deletes the
session. A tool budget allows at most six executions and two successful fixture predictions.
The API permits four concurrent agent runs per process. These limits constrain work; they
are not a hard billing cap. Cloud Run's own request logs may contain platform HTTP metadata;
our application logs omit prompt text, commentary and personal identifiers.

If Gemini fails after a tool succeeds, the API returns `partial` with the verified cards.
If it fails before a tool produces a result, it returns 503. If the request is ambiguous,
the agent can clarify and return `no_prediction`. The UI states that no prediction occurred.

## 9. Start the API and React app

Terminal A, repository root, environment active:

```bash
PYTHONPATH=backend uvicorn app.main:app --reload --port 8000 --no-access-log
```

Terminal B:

```bash
cd frontend
npm ci
npm run dev
```

Open http://localhost:5173. Vite proxies `/api` and `/health` to FastAPI, so no CORS allowlist
or embedded backend URL is necessary. In production, FastAPI serves the compiled React app
on the same origin as the API.

Try these actions:

1. Ask about Arsenal at home against Liverpool.
2. Compare that fixture with Man City at home against Chelsea.
3. Ask “Predict United against City” and check ambiguity handling.
4. Switch to **Direct model** and select the same fixture; numerical results should match.

The prediction cards are populated only by trusted Python tool results. Gemini's commentary
is displayed separately as generated text and may still be mistaken. Do not describe this
as a complete hallucination defence. Test the natural-language routing too: the agent could
select the wrong fixture even when the classifier's arithmetic is correct.

## 10. Run tests and a live smoke check

```bash
PYTHONPATH=backend python -m pytest backend/tests -q
cd frontend
npm run build
cd ..
```

The test suite uses real ADK tool execution with a scripted LLM, so it is repeatable and
does not consume Gemini tokens. It covers leakage, validation, cross-request isolation,
tool budgets and provider failure before/after prediction. This is not a test of Gemini's
actual reasoning. Complete the live check yourself:

```bash
curl --fail-with-body http://localhost:8000/api/analyse \
  -H 'Content-Type: application/json' \
  -d '{"message":"Predict Arsenal at home against Liverpool"}'
```

Expect `predictions` to contain the named fixture, `tool_calls` to include `predict_match`,
and a `model_version` on the card. Keep a screenshot for your release evidence.

Run the four-case real-provider smoke suite separately (it makes billable requests):

```bash
python evals/run_live_evals.py --url http://localhost:8000
```

Read `evals/live-report.json` and investigate failed cases. A passing small suite does not
establish production quality. Add representative cases and repeated runs before making that claim.

## 11. Run the production layout locally

After training and building React, the API also serves the compiled UI at http://localhost:8000.
For a container smoke test, stop anything using port 8080 and run:

```bash
docker compose up --build
```

Open http://localhost:8080 and use **Direct model**. Compose intentionally disables Gemini
because it has no credentials. The Cloud Run version uses the runtime service account;
the local non-container version uses ADC. Both execute the same application code.

## 12. Deploy and record

Continue in DEPLOY_GCP.md. Then use YOUTUBE_DEMO_GUIDE.md for an approximately 12-minute
video. Open docs/architecture.md in a Mermaid-capable editor for your system-design segment.
