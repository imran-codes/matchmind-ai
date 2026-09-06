# Deploy MatchMind with individual gcloud commands

This guide deploys the React frontend, FastAPI API, ADK agent and classifier as **one private
Cloud Run service**. Gemini runs through Vertex AI. Cloud Storage holds the approved model
release, Cloud Build builds the container, and Artifact Registry stores it.

There are no deployment shell scripts or Terraform in this learning route. Run one command
at a time, read the explanation, and check the result before continuing.

## Before you start

You need:

- A Google Cloud project with billing enabled.
- Google Cloud CLI installed.
- Permission to enable APIs, create service accounts, grant IAM roles, run builds and deploy Cloud Run.
- A Gemini model enabled for your project in Vertex AI Model Garden.
- The local build and tests completed from `BUILD_GUIDE.md`.

Commands beginning with `export` only create reusable terminal variables. They do not create
cloud resources. Replace the five values below before continuing.

## 1. Define your deployment values

```bash
export GCP_PROJECT="your-project-id"
export GCP_REGION="europe-west2"
export GCP_BUCKET="your-globally-unique-matchmind-bucket"
export RELEASE="v2-demo-001"
export GEMINI_MODEL="your-enabled-gemini-model-id"
```

Choose a new `RELEASE` value whenever the model, data, prompt or source changes.

Define the resource names used later:

```bash
export RUNTIME_SA="matchmind-runtime@${GCP_PROJECT}.iam.gserviceaccount.com"
export BUILD_SA="matchmind-build@${GCP_PROJECT}.iam.gserviceaccount.com"
export IMAGE="${GCP_REGION}-docker.pkg.dev/${GCP_PROJECT}/matchmind/app:${RELEASE}"
```

Verify them before they appear in resource-creation commands:

```bash
printf '%s\n' "$GCP_PROJECT" "$GCP_REGION" "$GCP_BUCKET" "$RELEASE" "$GEMINI_MODEL" "$IMAGE"
```

## 2. Authenticate the CLI

```bash
gcloud auth login
```

This authenticates your human account for `gcloud` operations.

```bash
gcloud config set project "$GCP_PROJECT"
```

This selects the target project for commands where the project is not repeated.

```bash
gcloud config set run/region "$GCP_REGION"
```

This sets the default Cloud Run region.

Confirm the active identity and project:

```bash
gcloud auth list --filter=status:ACTIVE
gcloud config get-value project
```

For local Python calls to Vertex AI, also create Application Default Credentials:

```bash
gcloud auth application-default login
gcloud auth application-default set-quota-project "$GCP_PROJECT"
```

Cloud Run will use its service account instead of this local credential.

## 3. Enable each Google Cloud API

Enable Service Usage first:

```bash
gcloud services enable serviceusage.googleapis.com --project="$GCP_PROJECT"
```

Enable Cloud Run:

```bash
gcloud services enable run.googleapis.com --project="$GCP_PROJECT"
```

Enable Cloud Build:

```bash
gcloud services enable cloudbuild.googleapis.com --project="$GCP_PROJECT"
```

Enable Artifact Registry:

```bash
gcloud services enable artifactregistry.googleapis.com --project="$GCP_PROJECT"
```

Enable Vertex AI:

```bash
gcloud services enable aiplatform.googleapis.com --project="$GCP_PROJECT"
```

Enable Cloud Storage, IAM, Logging, Monitoring and BigQuery:

```bash
gcloud services enable storage.googleapis.com --project="$GCP_PROJECT"
gcloud services enable iam.googleapis.com --project="$GCP_PROJECT"
gcloud services enable logging.googleapis.com --project="$GCP_PROJECT"
gcloud services enable monitoring.googleapis.com --project="$GCP_PROJECT"
gcloud services enable bigquery.googleapis.com --project="$GCP_PROJECT"
```

Verify the important APIs:

```bash
gcloud services list --enabled \
  --filter='NAME:(run.googleapis.com OR cloudbuild.googleapis.com OR artifactregistry.googleapis.com OR aiplatform.googleapis.com)'
```

## 4. Create Artifact Registry

```bash
gcloud artifacts repositories create matchmind \
  --project="$GCP_PROJECT" \
  --location="$GCP_REGION" \
  --repository-format=docker \
  --description="MatchMind application images"
```

This creates the private Docker repository used by Cloud Build.

Verify it:

```bash
gcloud artifacts repositories describe matchmind \
  --project="$GCP_PROJECT" \
  --location="$GCP_REGION"
```

If it already exists, describe and reuse it instead of creating a duplicate.

## 5. Create the Cloud Storage release bucket

```bash
gcloud storage buckets create "gs://${GCP_BUCKET}" \
  --project="$GCP_PROJECT" \
  --location="$GCP_REGION" \
  --uniform-bucket-level-access \
  --public-access-prevention
```

The bucket stores model artifacts and the Cloud Build source upload. It is not read during
each prediction because the approved model is packaged into the container image.

Verify the protection settings:

```bash
gcloud storage buckets describe "gs://${GCP_BUCKET}" \
  --format='yaml(name,location,iamConfiguration)'
```

## 6. Create separate service accounts

Create the Cloud Run runtime identity:

```bash
gcloud iam service-accounts create matchmind-runtime \
  --project="$GCP_PROJECT" \
  --display-name="MatchMind Cloud Run runtime"
```

Create the Cloud Build identity:

```bash
gcloud iam service-accounts create matchmind-build \
  --project="$GCP_PROJECT" \
  --display-name="MatchMind Cloud Build identity"
```

Verify both:

```bash
gcloud iam service-accounts list \
  --project="$GCP_PROJECT" \
  --filter='email:(matchmind-runtime OR matchmind-build)'
```

Keeping build and runtime identities separate prevents the running application from receiving
permissions to create images or modify releases.

## 7. Grant the runtime identity Vertex AI access

```bash
gcloud projects add-iam-policy-binding "$GCP_PROJECT" \
  --member="serviceAccount:${RUNTIME_SA}" \
  --role="roles/aiplatform.user" \
  --condition=None
```

This allows the ADK agent running in Cloud Run to call your enabled Gemini model through Vertex AI.
It does not give the runtime permission to upload containers or overwrite model artifacts.

## 8. Grant the build identity only its required roles

Allow it to read the release and staged source from the bucket:

```bash
gcloud storage buckets add-iam-policy-binding "gs://${GCP_BUCKET}" \
  --member="serviceAccount:${BUILD_SA}" \
  --role="roles/storage.objectViewer"
```

Allow it to write container images to this Artifact Registry repository:

```bash
gcloud artifacts repositories add-iam-policy-binding matchmind \
  --project="$GCP_PROJECT" \
  --location="$GCP_REGION" \
  --member="serviceAccount:${BUILD_SA}" \
  --role="roles/artifactregistry.writer"
```

Allow it to write build logs:

```bash
gcloud projects add-iam-policy-binding "$GCP_PROJECT" \
  --member="serviceAccount:${BUILD_SA}" \
  --role="roles/logging.logWriter" \
  --condition=None
```

Your human deployment account must be allowed to act as both service accounts. Capture its email:

```bash
export DEPLOYER_ACCOUNT="$(gcloud config get-value account)"
printf '%s\n' "$DEPLOYER_ACCOUNT"
```

Grant `actAs` on the build identity:

```bash
gcloud iam service-accounts add-iam-policy-binding "$BUILD_SA" \
  --project="$GCP_PROJECT" \
  --member="user:${DEPLOYER_ACCOUNT}" \
  --role="roles/iam.serviceAccountUser"
```

Grant `actAs` on the runtime identity:

```bash
gcloud iam service-accounts add-iam-policy-binding "$RUNTIME_SA" \
  --project="$GCP_PROJECT" \
  --member="user:${DEPLOYER_ACCOUNT}" \
  --role="roles/iam.serviceAccountUser"
```

In a bank, these bindings would normally be managed by the platform/IAM team or infrastructure
as code. If organization policy blocks a command, request the minimum role rather than widening
the runtime service account.

## 9. Train and test the release locally

Activate the clean Python 3.12 environment created in `BUILD_GUIDE.md`:

```bash
source .venv/bin/activate
```

Train the candidate models and generate release artifacts:

```bash
PYTHONPATH=backend python -m app.train
```

Run the automated tests:

```bash
PYTHONPATH=backend python -m pytest backend/tests -q
```

Build the React application:

```bash
cd frontend
npm ci
npm run build
cd ..
```

Inspect the release decision before uploading:

```bash
python -m json.tool backend/artifacts/metadata.json
```

Record the selected model, test metrics, data cut-off, limitations and model version.

## 10. Upload each immutable release artifact

Upload the trained estimator:

```bash
gcloud storage cp backend/artifacts/model.joblib \
  "gs://${GCP_BUCKET}/releases/${RELEASE}/model.joblib" \
  --if-generation-match=0
```

Upload the current team profiles:

```bash
gcloud storage cp backend/artifacts/profiles.json \
  "gs://${GCP_BUCKET}/releases/${RELEASE}/profiles.json" \
  --if-generation-match=0
```

Upload the model metadata and checksums:

```bash
gcloud storage cp backend/artifacts/metadata.json \
  "gs://${GCP_BUCKET}/releases/${RELEASE}/metadata.json" \
  --if-generation-match=0
```

Upload the data snapshot, dependency lock and agent definition for lineage:

```bash
gcloud storage cp backend/data/matches.csv \
  "gs://${GCP_BUCKET}/releases/${RELEASE}/matches.csv" \
  --if-generation-match=0
```

```bash
gcloud storage cp backend/requirements.lock \
  "gs://${GCP_BUCKET}/releases/${RELEASE}/requirements.lock" \
  --if-generation-match=0
```

```bash
gcloud storage cp backend/app/agent.py \
  "gs://${GCP_BUCKET}/releases/${RELEASE}/agent.py" \
  --if-generation-match=0
```

`--if-generation-match=0` refuses to overwrite an existing object. If the release name was
already used, inspect it and choose a new release name rather than silently replacing evidence.

Verify the release contents:

```bash
gcloud storage ls -l "gs://${GCP_BUCKET}/releases/${RELEASE}/"
```

## 11. Submit the Cloud Build

```bash
gcloud builds submit . \
  --project="$GCP_PROJECT" \
  --config=cloudbuild.yaml \
  --service-account="projects/${GCP_PROJECT}/serviceAccounts/${BUILD_SA}" \
  --gcs-source-staging-dir="gs://${GCP_BUCKET}/build-source" \
  --substitutions="_BUCKET=${GCP_BUCKET},_RELEASE=${RELEASE},_IMAGE=${IMAGE}"
```

Cloud Build downloads the approved release, installs locked dependencies, builds React and
pushes the container. It does not retrain the model.

Verify the image tag:

```bash
gcloud artifacts docker images describe "$IMAGE" \
  --project="$GCP_PROJECT"
```

Resolve the tag to an immutable digest:

```bash
export IMAGE_DIGEST="$(gcloud artifacts docker images describe "$IMAGE" \
  --project="$GCP_PROJECT" \
  --format='value(image_summary.digest)')"
```

Create the immutable image reference and inspect it:

```bash
export IMMUTABLE_IMAGE="${IMAGE%:*}@${IMAGE_DIGEST}"
printf '%s\n' "$IMMUTABLE_IMAGE"
```

The digest ties the deployment to exact container bytes. Do not proceed if it is empty or does
not begin with `sha256:`.

## 12. Deploy the private Cloud Run service

```bash
gcloud run deploy matchmind \
  --project="$GCP_PROJECT" \
  --region="$GCP_REGION" \
  --image="$IMMUTABLE_IMAGE" \
  --service-account="$RUNTIME_SA" \
  --no-allow-unauthenticated \
  --port=8080 \
  --memory=2Gi \
  --cpu=1 \
  --concurrency=4 \
  --timeout=90s \
  --min-instances=0 \
  --max-instances=2 \
  --set-env-vars="AGENT_ENABLED=true,GOOGLE_GENAI_USE_VERTEXAI=TRUE,GOOGLE_CLOUD_PROJECT=${GCP_PROJECT},GOOGLE_CLOUD_LOCATION=global,GEMINI_MODEL=${GEMINI_MODEL}"
```

This creates a private Cloud Run service. The same container serves React, FastAPI, the ADK
runner and the CPU classifier. The ADK deadline is 60 seconds, shorter than the Cloud Run timeout.

Verify the service configuration:

```bash
gcloud run services describe matchmind \
  --project="$GCP_PROJECT" \
  --region="$GCP_REGION" \
  --format='yaml(status.url,status.latestReadyRevisionName,spec.template.spec.serviceAccountName,spec.template.spec.containerConcurrency)'
```

## 13. Give your account permission to invoke the private service

```bash
gcloud run services add-iam-policy-binding matchmind \
  --project="$GCP_PROJECT" \
  --region="$GCP_REGION" \
  --member="user:${DEPLOYER_ACCOUNT}" \
  --role="roles/run.invoker"
```

This grants only your signed-in user access to call the service. It does not make it public.

## 14. Open the deployed service through an authenticated proxy

```bash
gcloud run services proxy matchmind \
  --project="$GCP_PROJECT" \
  --region="$GCP_REGION" \
  --port=8080
```

Keep that terminal open, then browse to:

```text
http://localhost:8080
```

Your browser reaches the deployed private Cloud Run service through your authenticated CLI session.

In a second terminal, check health:

```bash
curl --fail-with-body http://localhost:8080/health
```

Run a real ADK request:

```bash
curl --fail-with-body http://localhost:8080/api/analyse \
  -H 'Content-Type: application/json' \
  -d '{"message":"Predict Arsenal at home against Liverpool"}'
```

Run the small live behavioural suite, which consumes Gemini tokens:

```bash
source .venv/bin/activate
python evals/run_live_evals.py --url http://localhost:8080
```

Check fixture selection, tool calls, status, model version and probability totals. Automated
unit tests use a simulated model; this live step verifies your actual Gemini configuration.

## 15. Read Cloud Run application logs

```bash
gcloud run services logs read matchmind \
  --project="$GCP_PROJECT" \
  --region="$GCP_REGION" \
  --limit=30
```

The application logs status, latency, token counts, tool count, prompt version and classifier
version. It deliberately excludes raw questions and generated commentary.

## 16. Register the model in Vertex AI Model Registry

```bash
gcloud ai models upload \
  --project="$GCP_PROJECT" \
  --region="$GCP_REGION" \
  --display-name="matchmind-${RELEASE}" \
  --container-image-uri="$IMMUTABLE_IMAGE" \
  --artifact-uri="gs://${GCP_BUCKET}/releases/${RELEASE}" \
  --container-ports=8080 \
  --container-health-route=/health \
  --container-predict-route=/api/vertex/predict \
  --container-env-vars=AGENT_ENABLED=false \
  --description="Educational football classifier with versioned container and artifact lineage"
```

Registration records the custom serving container and artifact location. It does not create a
Vertex prediction endpoint or approve the model for production.

List the registry entry:

```bash
gcloud ai models list \
  --project="$GCP_PROJECT" \
  --region="$GCP_REGION" \
  --filter="displayName:matchmind-${RELEASE}"
```

## 17. Create the BigQuery analytics dataset

```bash
bq --project_id="$GCP_PROJECT" \
  --location="$GCP_REGION" \
  mk --dataset \
  --description="MatchMind operational events" \
  --default_table_expiration=2592000 \
  "${GCP_PROJECT}:matchmind_analytics"
```

The default table expiration is 30 days. Adjust it to your approved retention requirement.

Verify the dataset:

```bash
bq --project_id="$GCP_PROJECT" show "${GCP_PROJECT}:matchmind_analytics"
```

## 18. Create a filtered Logging sink into BigQuery

```bash
gcloud logging sinks create matchmind-events \
  "bigquery.googleapis.com/projects/${GCP_PROJECT}/datasets/matchmind_analytics" \
  --project="$GCP_PROJECT" \
  --use-partitioned-tables \
  --log-filter='resource.type="cloud_run_revision" AND resource.labels.service_name="matchmind" AND (jsonPayload.event="agent_request" OR jsonPayload.event="prediction_completed")'
```

Retrieve the sink identity:

```bash
export SINK_WRITER="$(gcloud logging sinks describe matchmind-events \
  --project="$GCP_PROJECT" \
  --format='value(writerIdentity)')"
```

Display it:

```bash
printf '%s\n' "$SINK_WRITER"
```

Dataset-level IAM is completed in BigQuery because `bq add-iam-policy-binding` supports tables
and views rather than datasets:

1. Open BigQuery in the Console.
2. Select `matchmind_analytics` and choose **Sharing → Permissions**.
3. Add the printed sink identity.
4. Grant **BigQuery Data Editor** on this dataset.
5. Generate new requests; logging sinks do not backfill earlier events.

## 19. Create a log-based failure metric

```bash
gcloud logging metrics create matchmind_agent_unavailable \
  --project="$GCP_PROJECT" \
  --description="Count MatchMind agent requests ending unavailable" \
  --log-filter='resource.type="cloud_run_revision" AND resource.labels.service_name="matchmind" AND jsonPayload.event="agent_request" AND jsonPayload.status="unavailable"'
```

Verify it:

```bash
gcloud logging metrics describe matchmind_agent_unavailable \
  --project="$GCP_PROJECT"
```

Create an alerting policy in Cloud Monitoring using
`logging.googleapis.com/user/matchmind_agent_unavailable`, connect your notification channel,
then trigger and verify it. Notification destinations and organizational alert standards require
your choice, so this guide does not invent them.

## 20. Inspect revisions and practise rollback

List the revisions:

```bash
gcloud run revisions list \
  --service=matchmind \
  --project="$GCP_PROJECT" \
  --region="$GCP_REGION"
```

After you have at least two revisions, route all traffic to a known-good previous revision:

```bash
gcloud run services update-traffic matchmind \
  --project="$GCP_PROJECT" \
  --region="$GCP_REGION" \
  --to-revisions="YOUR_PREVIOUS_REVISION=100"
```

Replace the placeholder with an exact revision returned by the list command. Rollback restores
the container code, prompt and classifier. It cannot reverse an external change behind a mutable
Gemini model identifier.

## 21. Stop the demo safely

Stop the local proxy with `Ctrl-C`. Cloud Run has zero minimum instances, but stored artifacts,
logs, images and other services may still incur costs.

If this is an isolated learning project and you no longer need the service, inspect its exact name
and then delete only that Cloud Run service:

```bash
gcloud run services delete matchmind \
  --project="$GCP_PROJECT" \
  --region="$GCP_REGION"
```

Review Model Registry, the Logging sink, BigQuery dataset, Artifact Registry and Cloud Storage
separately before removing anything. Do not delete a shared project or unrelated resources.

## What each GCP service contributes

| Service | Role in MatchMind |
|---|---|
| Vertex AI | Hosts Gemini used by the ADK agent |
| Cloud Run | Runs React, FastAPI, ADK and the classifier container |
| Cloud Build | Builds the tested release into a container image |
| Artifact Registry | Stores versioned container images |
| Cloud Storage | Stores data/model/dependency/prompt release evidence |
| Model Registry | Records the classifier container and artifact lineage |
| Cloud Logging | Captures application and platform events |
| Cloud Monitoring | Turns metrics into dashboards and alerts |
| BigQuery | Supports retained operational analysis from selected log events |

## Official command references

- Cloud Run deployment: https://docs.cloud.google.com/sdk/gcloud/reference/run/deploy
- Cloud Build submission: https://docs.cloud.google.com/sdk/gcloud/reference/builds/submit
- Cloud Run IAM binding: https://docs.cloud.google.com/sdk/gcloud/reference/run/services/add-iam-policy-binding
- Vertex AI model upload: https://docs.cloud.google.com/sdk/gcloud/reference/ai/models/upload
- Logging sink creation: https://docs.cloud.google.com/sdk/gcloud/reference/logging/sinks/create
