# Model and agent card

**Intended use:** Educational, hypothetical home/draw/away estimation and an ADK engineering
demonstration. Not a live fixture service or a validated decision-support product.

**Data:** The delivered CSV contains invented fixtures and scores for familiar team names.
Five synthetic seasons, seed 42. These are not historical football claims. Optional public
data ingestion has its own licensing, coverage, quality and freshness requirements.

**Classifier:** Class-prior baseline, multinomial logistic regression and histogram gradient
boosting are compared. Feature vector uses five-match form and pre-match Elo ratings.
Elo's initial rating, K factor and home offset are tutorial choices, not validated league parameters.
No neutral-venue input is supported. The model can learn home/away asymmetry from its labels
and positional features; a constant home-advantage feature would add no learned signal.

**Evaluation:** Chronological splits keep dates separate. Validation log loss determines
selection. Test reporting includes accuracy, log loss and the unhalved multiclass Brier score
(sum of squared class errors, averaged over matches). If the prior baseline wins, the UI
probabilities do not vary by fixture. There is no calibration fitting or uncertainty interval.

**Feature availability:** Rows use earlier dates only. Live/hypothetical inference uses final
saved profiles, with cut-off exposed on every card. Training state can span synthetic seasons;
production needs explicit handling of promotion, squad changes and season boundaries.

**Agent:** Gemini chooses from two allowlisted Python tools. Separate tests are needed for
team identification, home/away mapping, ambiguity, injection, tool usage and provider failures.
The generated commentary remains probabilistic. Displayed card values are captured from the
tool function, never parsed from commentary. Descriptive statistics are not feature attributions.

**Versions:** Estimator and profiles have SHA-256 checksums; model version derives from data,
artifacts and schema release. Metadata records scikit-learn version. Prompt version is
`football-analyst-v2`. Source/prompt/dependencies are additionally versioned by the deployed
container digest. A mutable provider model alias can change independently of our container.

**Limits:** No live news, injury data, line-ups, transfers, expected-goals feed or confirmed fixture
schedule. No guaranteed outcomes. Synthetic metrics are not evidence of real-world accuracy.
No PII is required. The model should not inform lending, employment or other consequential actions.

**Release evidence:** Retain metadata.json, test result, live-evaluation report, image digest,
configured Gemini ID, prompt version and an explicit reviewer decision. A small demo dataset
cannot establish fairness or production reliability.
