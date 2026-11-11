# Codex prompts to use **only after the preceding gate passes**

## Phase 2 — Engine and meter integration
Read the updated Phase 1 decision log and test evidence, `docs/ARCHITECTURE_CONTRACTS.md`, `docs/HARDWARE_INPUTS.md`, and the *exact pinned* vLLM source. Implement the smallest possible read-only state-observation and physical-energy adapter on the available Linux/NVIDIA testbed, document how the native engine admits/rejects work, and leave a safe failure path when no atomic gateway admission exists. Record hardware identities and sampling support. Run an idle + load + admission-failure smoke test. Do not claim paired replay or energy savings.

## Phase 3 — Physical paired counterfactuals
Implement independent repeated-prefix reconstruction: baseline omitted candidate vs one worker admitted candidate; same worker/testbed boundary and common H, random arm order, repeated pairs, state-fingerprint matching, raw energy measurements and rejection ledger. Start with five to ten tiny controlled states, not a large expensive sweep. Invalid state pairs must be recorded and excluded by predeclared rules. Deliver reproducible Parquet/JSON manifests, A/A variability, and whether physically distinguishable delta labels exist. Stop rather than fabricating any labels.

## Phase 4 — Learned incremental energy
With valid **measured** paired labels only, implement a baseline regression model and held-out trace/session evaluation. Add rank loss and uncertainty *only* as ablations once base model works. Measure MAE, signed delta prediction, candidate ranking, decision regret vs held-out pair oracle and total predictor overhead. Compare token, queue, cache and simple energy heuristics. If not better, report a negative result.

## Phase 5 — Safe router
Implement gateway selection with native acceptance and bounded stale/rejected retries. Verify no forced dispatch, trace preservation, same served model and SLO recording, and matching energy boundaries. Benchmark overhead under load and do not launch a large pilot until safety and state consistency pass.

## Phase 6–7 — Controlled and confirmatory study
Use pre-registered paired offered traces and strong baselines, randomized order, actual metered energy, all traffic denominators, TTFT/TPOT distribution and rejection. Pilot must estimate actual paired variance; lock fresh confirmatory sample sizes and error control before final runs. Present confidence intervals and all failures. Do not claim publishability based on isolated toy proofs.
