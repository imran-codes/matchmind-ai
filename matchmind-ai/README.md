# MatchMind AI — ADK edition (v2)

Build a Google ADK football analyst, connect it to a trained classifier and a React UI,
then deploy the complete application to Google Cloud Run. No Terraform required.

Start with **BUILD_GUIDE.md**, then **DEPLOY_GCP.md**. Film using **YOUTUBE_DEMO_GUIDE.md**.
Extract v2 into a fresh directory and create a fresh virtual environment; do not overlay v1.
The code is complete for the documented demo; live Gemini calls need your GCP project,
billing, an enabled model and credentials. The default local mode keeps the agent disabled
until you configure it, while the direct classifier works without Google Cloud.

## Fast local route (Python 3.12, Node 22.12+)

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r backend/requirements.lock
PYTHONPATH=backend python -m app.train
PYTHONPATH=backend python -m pytest backend/tests -q
cd frontend
npm ci
npm run build
cd ..
PYTHONPATH=backend uvicorn app.main:app --port 8000 --no-access-log
```

Open http://localhost:8000 and choose **Direct model**. Follow BUILD_GUIDE to enable ADK.

## What changed from v1

- A real ADK Agent and Runner call the typed `list_teams` and `predict_match` tools.
- React includes natural-language questions, two-fixture comparison and observed tool calls.
- Numerical cards come from validated tool results. Generated commentary is separate.
- Agent time, model calls, tool calls, fixture count and concurrent runs are bounded.
- Each application request has an isolated, disposable ADK session. No conversational memory.
- Removed the unsupported neutral-venue toggle and misleading confidence badges.
- Added a class-prior baseline and pre-match Elo features; all features use earlier dates only.
- Included data origin, snapshot date, artifact hashes and exact library versions.
- One container serves frontend/API/agent. Local Vite uses a same-origin API proxy.
- Training happens before release. Cloud Build consumes that release from Cloud Storage.
- Individual documented gcloud commands deploy privately, register the custom model container and set up log export.

## Implemented versus extensions

| Included and executable | Manual configuration included | Future work |
|---|---|---|
| ML training, ADK, API, UI, tests, Docker, Cloud Run scripts | GCP billing/IAM, Gemini selection, alert channel, BigQuery dataset share | Durable chat sessions, live data feed, production identity UX |
| Metadata, model registry registration, log export setup | Model/agent acceptance review, cost budget | Automated retraining, Vertex Pipelines, drift service, calibrated model attribution |

No RAG or CAG is needed for predicting from tabular team statistics. Add retrieval only if
you later introduce an approved football-document question-answering feature. ADK runs in
Cloud Run; Gemini runs on Vertex AI; the classifier runs locally in the container.

This is an educational engineering demo. Synthetic results do not establish predictive
power on real football. Review the data source's terms before switching to public match data.
