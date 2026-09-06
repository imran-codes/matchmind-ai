# Step-by-Step Guide

## 0. Demo order for YouTube

Use this exact order on camera so the walkthrough feels complete and easy to follow:

1. Open `README.md` and say what the project does.
2. Open `BUILD_GUIDE.md` and say this is the main setup path.
3. Open `backend/app/features.py` and explain how raw match history becomes model inputs.
4. Open `backend/app/train.py` and explain how the model is trained and saved.
5. Open `backend/app/prediction.py` and explain how the saved model is loaded for inference.
6. Open `backend/app/agent.py` and explain how the ADK agent is constrained to safe tools.
7. Open `backend/app/agent_runtime.py` and explain how each request gets its own session.
8. Open `backend/app/main.py` and explain the API routes and the frontend connection.
9. Open `backend/tests/` and show that the app is tested.
10. Open `frontend/src/App.tsx` and explain the UI and the Direct model / ADK tabs.
11. Show `backend/artifacts/` and explain that training creates the model files there.
12. Run the backend.
13. Run the frontend.
14. Run tests.
15. Run a live smoke check.
16. If using GCP, walk through the GCP setup section last.

Talking point:
- keep returning to the idea that the classifier does the scoring and the agent only helps interpret the request

---

## 1. Install and verify the tools

You first set up the basic tools the project needs:

1. Install **Python 3.12+**
2. Install **Node.js 22+**
3. Install **Git**
4. Install **Google Cloud CLI** if you want ADK / Vertex AI
5. Create and activate a virtual environment
6. Install the backend Python packages

Typical commands:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r backend/requirements.lock
node --version
python --version
```

If you are using the agent later, also verify:

```bash
gcloud --version
```

---

## 2. Inspect the data, build features, and train the model

This is the machine learning part.

### Inspect the data

You check the bundled match file before training:

```bash
python - <<'PY'
import pandas as pd
d = pd.read_csv('backend/data/matches.csv')
print(d.shape)
print(d.head(3).to_string(index=False))
print(d.FTR.value_counts(normalize=True))
PY
```

This tells you:
- how many rows exist
- what the columns look like
- how balanced the outcomes are

### Build features

The code in `backend/app/features.py` turns raw match history into model inputs.

In plain English:
- it looks at each team’s recent games
- it creates numbers like form, goals for/against, shots on target, and Elo
- it only uses **past** matches, never the current match result

### Train the model

Run:

```bash
PYTHONPATH=backend python -m app.train
```

This:
- loads the CSV
- builds the feature table
- splits the data into train / validation / test
- compares candidate models
- saves the best model into `backend/artifacts/`

The saved files are what the backend needs to run predictions.

---

## 3. Create the agent and understand it

The agent is the natural-language layer.

It lives in:
- `backend/app/agent.py`
- `backend/app/agent_runtime.py`

What it does:
- reads the user’s football question
- decides which tool to call
- uses `list_teams` to find valid team names
- uses `predict_match` to get a real classifier result

Important:
- the agent does **not** make up probabilities
- the real prediction comes from the trained model
- the agent just helps interpret the question and explain the result

If the agent is disabled, the app still works with the **Direct model**.

---

## 4. Configure Google Cloud for local ADK calls or use the direct model

You have two modes:

### Direct model

This works locally without Vertex AI.

Use it when you just want predictions and the frontend/backend to work.

### ADK agent mode

This needs Google Cloud and Vertex AI.

Typical setup:

```bash
cp .env.example gcp.env
set -a
source gcp.env
set +a
gcloud auth login
gcloud config set project "$GCP_PROJECT"
gcloud services enable aiplatform.googleapis.com
gcloud auth application-default login
gcloud auth application-default set-quota-project "$GCP_PROJECT"
```

Then set:

- `AGENT_ENABLED=true`
- `GEMINI_MODEL=...`

If you do not want to use GCP yet, just keep using **Direct model**.

---

## 5. Run the ADK development interface and understand the API runner

### ADK development interface

This is the local agent debugging UI.

Run:

```bash
PYTHONPATH=backend adk web backend/agents --port 8001
```

This lets you:
- talk to the agent directly
- see tool calls
- inspect the agent’s response flow

### API runner

The API runner is the backend endpoint that handles one request at a time.

It:
- creates a fresh session
- runs the agent
- collects tool outputs
- returns the final analysis response

The key file is `backend/app/agent_runtime.py`.

---

## 6. Start the API and React app

### Backend

From the project root:

```bash
source .venv/bin/activate
PYTHONPATH=backend uvicorn app.main:app --reload --port 8000 --no-access-log
```

### Frontend

In another terminal:

```bash
cd frontend
npm ci
npm run dev
```

Then open the Vite URL, usually:

```text
http://localhost:5173
```

The frontend talks to the backend through the Vite proxy.

If the backend fails because artifacts are missing, train the model first.

---

## 7. Run tests and a live smoke check

### Backend tests

```bash
PYTHONPATH=backend python -m pytest backend/tests -q
```

### Frontend build check

```bash
cd frontend
npm run build
```

### Live smoke check

```bash
curl --fail-with-body http://localhost:8000/api/analyse \
  -H 'Content-Type: application/json' \
  -d '{"message":"Predict Arsenal at home against Liverpool"}'
```

### Real-provider smoke suite

```bash
python evals/run_live_evals.py --url http://localhost:8000
```

This checks the live agent path if Vertex AI is enabled.

---

## 8. Run the production layout locally, deploy, and record

### Production layout locally

After training and building the frontend, the backend can serve the compiled React app too.

Run:

```bash
docker compose up --build
```

Then open the app on the port that Compose prints.

### Deploy

Use:
- `DEPLOY_GCP.md`
- `BUILD_GUIDE.md`

for the cloud steps.

### Record

Use:
- `YOUTUBE_DEMO_GUIDE.md`

for the demo recording flow.

---

## 9. Machine learning lifecycle, based on Google-style workflow

### 1. Ideate

Decide what problem you are solving:
- football outcome prediction
- direct model plus optional agent
- what the app should and should not do

### 2. Prepare

Get the data and environment ready:
- inspect the CSV
- validate the rows
- create the virtual environment
- install dependencies

### 3. Build

Create the model pipeline:
- build features
- train candidate models
- save the best one

### 4. Evaluate

Check whether the model is good enough:
- validation metrics
- test metrics
- live smoke checks
- backend tests

### 5. Deploy

Put the app where users can access it:
- local Docker compose
- Cloud Run / GCP deployment

### 6. Operate

Run and monitor the system:
- API health
- logs
- agent requests
- prediction responses

### 7. Improve

Make it better over time:
- refine features
- retrain with better data
- improve the agent prompts
- add safer deployment checks

---

## 10. GCP setup and deployment checklist

Use this section when you are ready to move from local work to Google Cloud.

### 10.1 Define project, region, bucket, release, and Gemini model

Start every terminal session with variables:

```bash
export PROJECT_ID="your-project-id"
export REGION="europe-west2"

export SERVICE_NAME="ai-classifier-agent"
export REPOSITORY="ai-services"

export BUCKET="${PROJECT_ID}-ml-artifacts"

export RELEASE="v1.0.0"

export IMAGE_NAME="ai-classifier-agent"

export GEMINI_MODEL="gemini-3.5-flash"
```

Then configure gcloud:

```bash
gcloud config set project $PROJECT_ID
gcloud config set run/region $REGION
gcloud config list
```

Why:
- the variables keep commands repeatable
- they reduce the risk of deploying to the wrong project
- they make it obvious which version, region, and model you are using

---

### 10.2 Authenticate with Google Cloud

Authenticate the CLI:

```bash
gcloud auth login
gcloud auth list
```

Authenticate your local code with Application Default Credentials:

```bash
gcloud auth application-default login
gcloud auth application-default set-quota-project $PROJECT_ID
```

Why there are two logins:
- `gcloud auth login` is for the CLI
- `gcloud auth application-default login` is for local Python code that talks to Google APIs

---

### 10.3 Enable Google Cloud APIs

Enable the services one by one while learning:

```bash
gcloud services enable run.googleapis.com
gcloud services enable cloudbuild.googleapis.com
gcloud services enable artifactregistry.googleapis.com
gcloud services enable aiplatform.googleapis.com
gcloud services enable storage.googleapis.com
gcloud services enable logging.googleapis.com
gcloud services enable monitoring.googleapis.com
gcloud services enable bigquery.googleapis.com
gcloud services enable iam.googleapis.com
gcloud services list --enabled
```

Why:
- Google Cloud APIs are opt-in
- this keeps the project smaller, safer, and easier to reason about

---

### 10.4 Create Artifact Registry

Create a Docker repository:

```bash
gcloud artifacts repositories create $REPOSITORY \
  --repository-format=docker \
  --location=$REGION \
  --description="Container images for AI services"
```

Check:

```bash
gcloud artifacts repositories list
```

Why:
- Artifact Registry stores versioned container images
- Cloud Build builds the image
- Cloud Run runs the image

---

### 10.5 Create a protected Cloud Storage bucket

Create the bucket:

```bash
gcloud storage buckets create gs://$BUCKET \
  --project=$PROJECT_ID \
  --location=$REGION \
  --uniform-bucket-level-access \
  --public-access-prevention
```

Check it:

```bash
gcloud storage buckets describe gs://$BUCKET
```

Optional object versioning:

```bash
gcloud storage buckets update gs://$BUCKET \
  --versioning
```

Why:
- store model artefacts in a versioned, protected place
- use IAM instead of object ACLs

---

### 10.6 Create separate build and runtime service accounts

Create the build identity:

```bash
gcloud iam service-accounts create ai-build-sa \
  --display-name="AI Build Service Account"
```

Create the runtime identity:

```bash
gcloud iam service-accounts create ai-runtime-sa \
  --display-name="AI Runtime Service Account"
```

Define variables:

```bash
export BUILD_SA="ai-build-sa@${PROJECT_ID}.iam.gserviceaccount.com"
export RUNTIME_SA="ai-runtime-sa@${PROJECT_ID}.iam.gserviceaccount.com"
```

Why:
- build and runtime should not have the same permissions
- this follows least privilege and separation of duties

---

### 10.7 Grant runtime access to Vertex AI and Storage

Grant Vertex AI access:

```bash
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:$RUNTIME_SA" \
  --role="roles/aiplatform.user"
```

If the runtime must read model files from Storage:

```bash
gcloud storage buckets add-iam-policy-binding gs://$BUCKET \
  --member="serviceAccount:$RUNTIME_SA" \
  --role="roles/storage.objectViewer"
```

Why:
- the Cloud Run app should run as the runtime service account
- it should not depend on your personal account

---

### 10.8 Grant build account access to build services

Artifact Registry:

```bash
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:$BUILD_SA" \
  --role="roles/artifactregistry.writer"
```

Storage:

```bash
gcloud storage buckets add-iam-policy-binding gs://$BUCKET \
  --member="serviceAccount:$BUILD_SA" \
  --role="roles/storage.objectViewer"
```

Logging:

```bash
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:$BUILD_SA" \
  --role="roles/logging.logWriter"
```

Cloud Build worker:

```bash
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:$BUILD_SA" \
  --role="roles/cloudbuild.builds.builder"
```

Why:
- the build account only needs build-time permissions
- the runtime account only needs runtime permissions

---

### 10.9 Train and test locally first

Before cloud deployment, verify everything locally:

```bash
PYTHONPATH=backend python -m app.train
PYTHONPATH=backend python -m pytest backend/tests -q
PYTHONPATH=backend uvicorn app.main:app --reload --port 8000 --no-access-log
```

Why:
- local debugging is cheaper and faster than cloud debugging
- the classifier is trained locally
- Gemini/ADK is configured separately

---

### 10.10 Upload a versioned model artefact

Upload the trained model:

```bash
gcloud storage cp \
  model/model.joblib \
  gs://$BUCKET/models/classifier/$RELEASE/model.joblib
```

Check:

```bash
gcloud storage ls \
  gs://$BUCKET/models/classifier/$RELEASE/
```

Why:
- versioned model files make rollback and audit easier

---

### 10.11 Submit Cloud Build

Set the image URI:

```bash
export IMAGE_URI="${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPOSITORY}/${IMAGE_NAME}"
```

Submit the build:

```bash
gcloud builds submit \
  --config=cloudbuild.yaml \
  --service-account="projects/$PROJECT_ID/serviceAccounts/$BUILD_SA" \
  --substitutions="_IMAGE=$IMAGE_URI,_RELEASE=$RELEASE"
```

Then check the pushed image:

```bash
gcloud artifacts docker images list \
  ${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPOSITORY}
```

Why:
- Cloud Build gives you a repeatable container build instead of “built on my laptop”

---

### 10.12 Resolve the image digest

Get the immutable digest:

```bash
export IMAGE_DIGEST=$(gcloud artifacts docker images describe \
  ${IMAGE_URI}:${RELEASE} \
  --format="value(image_summary.digest)")
```

Create an immutable reference:

```bash
export IMMUTABLE_IMAGE="${IMAGE_URI}@${IMAGE_DIGEST}"
echo $IMMUTABLE_IMAGE
```

Why:
- tags are labels
- digests identify the exact bytes you are deploying

---

### 10.13 Deploy private Cloud Run

Deploy the service:

```bash
gcloud run deploy $SERVICE_NAME \
  --image=$IMMUTABLE_IMAGE \
  --region=$REGION \
  --service-account=$RUNTIME_SA \
  --no-allow-unauthenticated \
  --set-env-vars="GOOGLE_CLOUD_PROJECT=$PROJECT_ID,GOOGLE_CLOUD_LOCATION=$REGION,GEMINI_MODEL=$GEMINI_MODEL,MODEL_RELEASE=$RELEASE,MODEL_BUCKET=$BUCKET" \
  --memory=1Gi \
  --cpu=1 \
  --min=0 \
  --max=10
```

Why:
- keep the service private
- use the runtime service account
- pass only the environment variables the app needs

---

### 10.14 Grant yourself Cloud Run Invoker

Get your account:

```bash
export USER_EMAIL=$(gcloud config get-value account)
```

Grant access:

```bash
gcloud run services add-iam-policy-binding $SERVICE_NAME \
  --region=$REGION \
  --member="user:$USER_EMAIL" \
  --role="roles/run.invoker"
```

Why:
- only authenticated users with permission can call the service

---

### 10.15 Open the private service locally

Use the authenticated proxy:

```bash
gcloud run services proxy $SERVICE_NAME \
  --region=$REGION \
  --port=8080
```

Then open:

```text
http://localhost:8080
```

Or call the service with an identity token:

```bash
curl \
  -H "Authorization: Bearer $(gcloud auth print-identity-token)" \
  "$SERVICE_URL/health"
```

---

### 10.16 Run live ADK evaluation

Run live checks against the deployed service:

```bash
python evals/run_live_evals.py --url http://localhost:8000
```

Why:
- this tests the deployed path, not just local unit tests
- it catches permission, env var, and network issues

---

### 10.17 Read Cloud Run logs

Read recent logs:

```bash
gcloud run services logs read $SERVICE_NAME \
  --region=$REGION \
  --limit=100
```

Tail live logs:

```bash
gcloud run services logs tail $SERVICE_NAME \
  --region=$REGION
```

Or query Cloud Logging:

```bash
gcloud logging read \
  "resource.type=cloud_run_revision AND resource.labels.service_name=$SERVICE_NAME" \
  --limit=50
```

Why:
- logs tell you what happened
- metrics tell you how often it happens

---

### 10.18 Register the classifier in Vertex AI Model Registry

If you want registry tracking for the classifier:

```bash
gcloud ai models upload \
  --region=$REGION \
  --display-name="mortgage-document-classifier" \
  --artifact-uri="gs://$BUCKET/models/classifier/$RELEASE/"
```

Why:
- Storage holds files
- Model Registry gives those files model lifecycle and governance

---

### 10.19 Create a BigQuery analytics dataset

Create a dataset:

```bash
bq --location=$REGION mk \
  --dataset \
  "${PROJECT_ID}:ai_observability"
```

Check datasets:

```bash
bq ls
```

Why:
- BigQuery is useful for longer-term analysis of requests, evaluations, and metrics

---

### 10.20 Create Logging sink and monitoring metric

Create a logging sink:

```bash
gcloud logging sinks create ai-bigquery-sink \
  bigquery.googleapis.com/projects/$PROJECT_ID/datasets/ai_observability \
  --log-filter="resource.type=cloud_run_revision AND resource.labels.service_name=$SERVICE_NAME"
```

Create an error metric:

```bash
gcloud logging metrics create ai_service_errors \
  --description="Cloud Run AI service errors" \
  --log-filter='
resource.type="cloud_run_revision"
resource.labels.service_name="'$SERVICE_NAME'"
severity>=ERROR'
```

Why:
- sinks move logs into BigQuery
- metrics help alert on errors

---

### 10.21 Inspect revisions and practise rollback

List revisions:

```bash
gcloud run revisions list \
  --service=$SERVICE_NAME \
  --region=$REGION
```

Describe one:

```bash
gcloud run revisions describe \
  ai-classifier-agent-00002 \
  --region=$REGION
```

Rollback traffic:

```bash
gcloud run services update-traffic $SERVICE_NAME \
  --region=$REGION \
  --to-revisions=ai-classifier-agent-00002=100
```

Why:
- every deployment creates a new revision
- traffic splitting and rollback are part of safe release practice
