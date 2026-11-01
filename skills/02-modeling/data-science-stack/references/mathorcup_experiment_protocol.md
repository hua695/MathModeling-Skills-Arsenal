# MathorCup experiment protocol

Use with the existing task card, model cards, evaluation protocol and run manifest. This reference owns experimental detail; contest-orchestrator owns task scope, approvals and final claims.

## Metrics and sample provenance

Before comparing candidates, define the metric's target units/scales, target weights, group weights, missing-target rule, and out-of-fold aggregation order. Equal weighting of all targets is not equal weighting of target groups with different sizes. Distinguish averaging per-run metrics from scoring averaged predictions; name both explicitly when both are reported. A display table is not automatically an evaluation dataset.

Retain sample-level source and use: model-fit membership, preprocessing-fit membership, model-selection exposure, evaluation role and prediction source. Not fitting a sample's label does not establish a blind test if that label influenced model selection. Mixed-source display rows cannot be pooled and presented as one independent validation set. Verify actual entity keys from original tables rather than rounded/scientific-notation display strings.

Predeclare candidate acceptance, comparison families and uncertainty method in the existing evaluation plan. Repeated-CV folds are dependent; do not treat fold scores as independent replicates for an arbitrary interval or significance claim. Use a defensible paired/resampling design with its assumptions, or report descriptive variability without claiming inferential coverage. Candidate rejection because the adoption criterion was not met is a scientific result, not an implementation failure.

## Estimator capabilities and ablations

Record installed package version, estimator class, actual objective/loss, target shape, multi-output strategy, and number of fits. Inspect the installed API/signature and run a small shape smoke test before assuming support. For externally verified API facts, use the current official documentation for that installed version. Do not infer target coupling from a two-dimensional predict API, or infer lack of support from a wrapper used in an older project. Explain whether the objective/structure actually couples target responses.

Compare algorithms under the same split and metric; compare representations separately. For each transform, state whether it adds information or only rescales existing variables, how its constants were obtained and whether they were learned inside training folds. Mathematical monotonicity arguments do not establish bit-for-bit behavior of finite-precision/histogram implementations. Test the actual implementation without inventing a universal benefit or invariance rule.

Unverified sentinel semantics require matched-population sensitivity branches, not a guessed physical interpretation. Name keeping, missing-value replacement and column-dropping diagnostics separately. Calibration constants must be recomputed from the appropriate source population; continuous mappings do not create true ordinal ground truth. Distinguish macro and pooled ordinal metrics, and relative quantile position from absolute calibrated grades.

For attribution, distinguish single-field dependence, group dependence, group-size normalization and causation. Stability frequencies are descriptive unless a statistical probability interpretation has been justified. For generated/optimized scenarios, report both changed-field count and standardized displacement; distinguish total, searched, candidate and jointly accepted denominators. Original chemical/physical constraints and sensory proxy checks remain separate.

## Time, memory and restart behavior

Record time budget and memory guard separately in the existing experiment configuration. Removing a time cap leaves memory protection active. Measure per-worker peak memory, current system headroom and internal thread count on the actual machine before setting concurrency; do not copy fixed memory values from a previous competition.

When headroom is insufficient, stop launching workers or checkpoint owned work; never close the user's unrelated applications. Parallelize independent calculations only. Manifest, checkpoint and gate writes have one owner and occur serially. Use atomic replace for completed checkpoint records when implementing a runner.

Resume by data/code/config/seed identity and skip only matching completed units. Keep interrupted or failed units explicit. Rank candidates only after the declared comparable protocol is complete; a mean over whichever folds happened to finish cannot compete against a complete run. If the user accepts a partial experiment, report its scope and limitations instead of silently altering the denominator. Keep the raw-data training entry usable without approval JSON or original-project caches.
