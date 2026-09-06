# Release and post-deployment checklist

This is the next-step checklist for a production team; the table distinguishes demo controls
from work still required. A weekend is enough to demonstrate the mechanics, not to complete
banking governance, service reliability validation and operational ownership.

| Area | Implemented in this demo | Required before a real service |
|---|---|---|
| Data | Synthetic snapshot, schema/range/label checks, hashes | Licensed source, data owner, freshness SLA, retention and cold-start policy |
| ML quality | Prior baseline, chronological evaluation, log loss/Brier | Representative holdout, calibration, segment/error analysis, attribution if claimed |
| Agent | Allowlisted tools, schema validation, call/time/fixture bounds | Live behavioural evals, prompt-injection red team, explicit acceptable failure thresholds |
| Isolation | Per-request disposable session | Auth-bound durable sessions if conversational memory is introduced |
| Identity | Private Cloud Run, dedicated service accounts, ADC | End-user identity UX, organization policies, access review and abuse controls |
| Delivery | Locked dependencies, verified artifacts, image digest | Dependency/image vulnerability scan gates, provenance/signing, staged rollout/approval |
| Operations | Structured logs, log sink, manual alert setup | SLO burn-rate alerts, on-call routing, incident drills, cost and quota controls |
| Explainability | Clear data origin/cut-off; separate commentary | Evaluated explanations and user understanding; no unsupported attribution claims |
| Model Registry | Custom container registration with artifact URI | Parent versions, evaluation records, approvals, lineage integration and retirement |
| Post-deployment | Live-eval script and rollback instructions | Automated scheduled evals/drift checks with accountable response owners |

## Candidate recurring pipelines

| Trigger | Pipeline | Response |
|---|---|---|
| New dataset | Validate, build point-in-time features, train/evaluate | Quarantine invalid inputs; do not replace production artifacts |
| Prompt/SDK/model change | Unit/contract tests and live agent evals | Block promotion on tool/fixture/grounding regressions |
| After deployment | Real request, known fixture, exact card comparison | Investigate; roll back if release caused regression |
| Nightly, after measuring cost | Small fixed and rotating agent eval set | Alert on sustained behavioural regression, not one noisy score |
| Once outcomes are known | Join saved pre-match predictions to actual results | Recalculate calibration/log loss by segment and time |
| Feature distribution shift | Drift analysis plus data-quality diagnosis | Review causes; drift alone does not justify automatic retraining |
| Provider errors/cost jump | Latency, availability and token monitoring | Apply bounded retries, fall back to direct model or disable agent |

These schedules are examples, not natural drift intervals. Cloud Scheduler + Cloud Run Jobs
or Vertex AI Pipelines are follow-on implementation choices. This repository does not silently
retrain or promote a new model. No real outcomes are currently collected, so production
calibration drift cannot be measured from these logs alone.
