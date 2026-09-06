# YouTube: Build and deploy a Google ADK football agent

Suggested title: **Build an AI Football Agent with Google ADK — Python to Cloud Run**.
Target 12–15 minutes. The story is: natural-language request → ADK tool call → classifier
probabilities → observable cloud deployment. Give the code as a download so viewers can
follow BUILD_GUIDE and DEPLOY_GCP rather than copying commands from fleeting frames.

## Before recording

1. Complete the live Gemini smoke test. Confirm tool calls and the named fixture.
2. Run the authenticated `gcloud run services proxy` command from DEPLOY_GCP.md and open
   http://localhost:8080 for the deployed app.
3. In a separate terminal, start `PYTHONPATH=backend adk web backend/agents --port 8001` if
   you want to show the development UI's event inspector. This is a local developer view.
4. Prepare tabs for the deployed UI, agent.py, agent_runtime.py, metadata.json, architecture
   diagram, Cloud Run service and Logs Explorer. Hide identity, project and billing details.
5. Keep a previously recorded successful request clip as backup. Label replayed footage honestly;
   do not present a mock response or direct-model call as a live ADK call.

## 0:00–0:35 — Show the outcome first

On screen: enter “Predict Arsenal at home against Liverpool. Explain the limitations.”
Click **Ask the ADK agent**. Pause on the three probability bars and tool activity.

Say:

> I asked a football question in plain English. Google's ADK agent chose a Python tool,
> and a trained classifier calculated these three probabilities. Let me show you how the
> agent, model and cloud deployment fit together.

Point to the synthetic-data badge. Do not describe the score as real-world predictive accuracy.

## 0:35–1:20 — Model versus agent

On screen: online architecture diagram in docs/architecture.md.

Say:

> Gemini understands the request. ADK coordinates tool calls. The classifier produces the
> probabilities. The React app displays the structured tool result and keeps generated
> commentary separate, because an LLM can still make mistakes in its explanation.

## 1:20–2:05 — Project setup

Show BUILD_GUIDE steps 2–4 and the file tree. Run the version checks and point to the locks.

Say:

> I use Python 3.12 for the agent and model, and React with TypeScript for the interface.
> Dependency locks keep the training and serving environments aligned. The data is synthetic
> so anyone can reproduce the first build without needing a football-data account.

## 2:05–4:05 — Create the ADK agent

Open `backend/app/agent.py`. Reveal the instruction, list_teams, predict_match and Agent
constructor in that order. Show these actual files rather than a simplified different implementation.

Say:

> These ordinary Python functions become tools through their names, type hints and docstrings.
> The model can choose one and supply arguments. The function still validates those arguments.
> Instructions describe behaviour, but the Python boundary enforces what the tool can actually do.

Then:

> I use one agent with two tools. I don't need sub-agents until there are separate specialist
> responsibilities that justify the additional coordination and evaluation.

## 4:05–5:05 — Watch tool calling happen

Open the local ADK development UI at port 8001 and ask the fixture question. Inspect the
function-call arguments and function-response payload.

Say:

> Here is the observable sequence: Gemini requested predict_match with Arsenal as home and
> Liverpool as away. The Python function returned the model version, data date and probabilities.
> This is a tool event, not the model's hidden reasoning.

If Gemini first calls list_teams, include that in the narration. Tool order is not hard-coded.

## 5:05–6:15 — Explain the classifier

Open features.py, then run `PYTHONPATH=backend python -m app.train` in the local repository.

Say:

> Each training row uses form and Elo information from earlier dates. Elo summarizes longer-term
> results; the last five matches capture recent form. I compare simple outcome frequencies,
> logistic regression and gradient boosting. Validation log loss selects the model.

Read the actual winner and metrics on screen. Explain that the prior baseline can legitimately
win. Do not hard-code a promised percentage into your script or thumbnail.

## 6:15–7:10 — Show why leakage matters

Highlight the two loops per date in features.py: first build rows, then update team state.

Say:

> I don't know kick-off times in this dataset, so no match uses another result from the same date.
> The chronological split also keeps dates separate. A random split or current-match statistics
> could make a model look impressive while making its evaluation unreliable.

## 7:10–8:30 — Demonstrate the product

Return to the deployed application through port 8080:

1. Ask the two-fixture comparison example.
2. Inspect the observed tool names and separate prediction cards.
3. Ask an ambiguous question and show whether the agent asks for clarification.
4. Switch to **Direct model** and select Arsenal/Liverpool. The classifier probabilities should match.

Say:

> Removing the agent leaves the classifier working. Adding the agent improves how a user
> expresses the task, but it does not automatically improve the statistical prediction.

Every main-app request is independent. If an ambiguous request needs clarification, re-enter
the complete fixture; don't imply the app has persistent conversational memory.

## 8:30–9:35 — Guards and failure handling

Show schemas.py, runtime timeout and tests/test_agent.py. Run the tests.

Say:

> The tests execute ADK's real runner with a simulated LLM, including a deliberately fabricated
> percentage. It cannot replace the card's tool-generated numbers. A provider failure after
> successful inference preserves the card as a partial response. A failure before inference
> returns an explicit unavailable status.

Explain that a simulated LLM verifies plumbing, not Gemini's actual reasoning. The live-evaluation
script tests fixture selection against the configured provider and has separate evidence.

## 9:35–11:10 — Deploy everything to GCP

Show the offline architecture and the individual gcloud commands. Builds take time, so cut between command
submission and the actual successful build; don't speed through credentials or permissions.

Say:

> I train and test first, upload a versioned release to Cloud Storage, then Cloud Build packages
> that exact model with the agent and frontend. Artifact Registry stores the container and Cloud
> Run deploys an image digest. The runtime service account calls Gemini on Vertex AI without a key file.

Then show the proxy:

> This browser address is a local authenticated proxy to my private Cloud Run service. The
> application is deployed on Google Cloud, while my identity controls access for this demo.

## 11:10–12:15 — Registry and observability

Show the Model Registry entry and its artifact URI. Make a fresh request and find its
`agent_request` log event. Optionally show BigQuery after the sink has received events.

Say:

> Registry registration records the serving container and artifact lineage; it doesn't magically
> approve the model or deploy an endpoint. Logs record request status, latency, token usage and
> versions without storing the question text. Alerting and BigQuery analysis help us notice regressions.

## 12:15–13:00 — Finish as an AI lead

Show docs/production-checklist.md.

Say:

> As a lead, I want to know who owns the data, what beats the baseline, how the agent is evaluated,
> what identity can call each service and how we roll back. This project demonstrates those
> engineering boundaries. A production service still needs representative data, approved use,
> operational ownership and stronger release gates.

Close on a real prediction card. Invite a specific next feature such as an approved news source
or outcome-based calibration monitoring, rather than promising guaranteed predictions.

## Description and recording notes

- Link the source package, build/deployment guides and official ADK documentation.
- State that the included match dataset is synthetic and probabilities are educational estimates.
- If switching to public match data, provide its attribution and comply with its usage terms.
- Use terminal fonts large enough for a 1080p viewer. Do not expose credentials or account details.
- Label local ADK Dev UI, deployed app, simulated tests and replay footage accurately.
- Thumbnail: **BUILD A FOOTBALL AI AGENT** with the three outcome bars and a short ADK → tool graphic.
