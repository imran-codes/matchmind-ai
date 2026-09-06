# MatchMind ADK architecture

## Online request path — implemented

```mermaid
flowchart TB
    Browser["Browser"] --> Access["Authenticated gcloud proxy"]
    Access --> Run["Cloud Run: one private service"]
    subgraph Container["Application container"]
      UI["React interface"] --> API["FastAPI: schema and request limits"]
      API --> Agent["ADK agent and isolated Runner"]
      API -->|"Direct model route"| Classifier["Classifier and team profiles"]
      Agent --> Tools["Python tools: team list and prediction"]
      Tools --> Classifier
      Classifier --> Cards["Validated numerical cards"]
      Cards --> UI
      Agent --> Text["Separate generated commentary"]
      Text --> UI
    end
    Run --> UI
    Agent <-->|"Runtime identity"| Vertex["Gemini on Vertex AI"]
    API --> Logs["Cloud Logging"]
    Logs --> Metrics["Monitoring metrics and alerts"]
    Logs --> Sink["Filtered log sink"]
    Sink --> BQ["BigQuery analytics"]
```

The authenticated proxy is a recording/development access method. A commercial frontend
would need a customer identity design; do not expose the agent anonymously just to film it.
ADK is a Python framework inside Cloud Run, not a separately deployed foundation model.
The classifier uses CPU inference in that same container. Gemini is a managed API dependency.

## Offline training and deployment path — implemented scripts

```mermaid
flowchart TB
    CSV["Synthetic or licensed match data"] --> Quality["Validate data contract"]
    Quality --> Features["Prior-date form and Elo features"]
    Features --> Split["Chronological train / validation / test"]
    Split --> Train["Prior baseline, logistic, boosting"]
    Train --> Select["Select by validation log loss"]
    Select --> Test["Report holdout metrics and run tests"]
    Test --> Review["Human review: quality and limitations"]
    Review --> GCS["Cloud Storage release snapshot"]
    Source["Source, prompt and dependency locks"] --> Build["Cloud Build"]
    GCS -->|"Download approved artifacts"| Build
    Build --> Images["Artifact Registry image digest"]
    Images --> Deploy["Cloud Run revision"]
    Images --> Registry["Vertex AI Model Registry entry"]
    GCS --> Registry
    Deploy --> Live["Live ADK smoke and evaluation"]
    Live --> Decision["Keep revision or roll back"]
```

The human review and live-check gates are manual in this tutorial. Do not claim they are
enforced by a CI/CD approval system. Model Registry registration does not start training,
create a prediction endpoint or automatically approve the model.

## Responsibility map for an AI/MLE lead

| Owner | Deliverable | Question the lead should ask |
|---|---|---|
| Data engineering | Validated, licensed snapshot | Can any feature use information unavailable at prediction time? |
| Data science | Baselines, features and evaluation | Does this outperform simple outcome frequencies on later data? |
| ML engineering | Versioned artifact and serving contract | Can we reproduce and roll back the exact estimator and preprocessing? |
| AI engineering | ADK tools, prompt and evaluation | Can the agent select the wrong fixture or invent an unsupported action? |
| QE | Failure, contract and behavioural tests | What is simulated, and what was tested against the live model? |
| Platform/SRE | IAM, image delivery and observability | Which identity can access each dependency, and what alerts reach an owner? |
| Product/governance | Intended use and release decision | Do users see the data cut-off, uncertainty and limitations? |

## Why no RAG, CAG or Terraform here?

The prediction features are structured numbers. No document knowledge base is needed for
the current job. Caching stable context would only be justified by measured reuse, latency
and cost. Terraform would help reproduce infrastructure across team environments, but the
numbered gcloud commands teach the same underlying resources with less initial setup.
