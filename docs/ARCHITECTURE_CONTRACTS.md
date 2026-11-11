# Architecture contracts — implementable v7 specification

## Objective and estimand
For immutable request `r`, observed initial state `S`, candidate worker `w`, and common horizon `H`:

**Canonical sign:** `delta_E = E_admit_w(S,r; H) - E_omit(S; H)` in Joules. Negative values are legal. **Never flip this sign in datasets or ranking.** This is a *local isolated-busy-period* intervention by default (no further arrivals); explicitly flag any future-arrival extension as a different estimand.

Use same initial cache, request prefix, model weights, runtime flags, clocks within a registered band, total physical metering boundary and horizon. Measure until both paths drain and use common H; record if this is impossible under replay budget. Record any dynamic execution differences and censor invalid pairs rather than making up deltas.

## Offline pipeline contracts

`RequestRecord`: ID, trace/session ID, immutable tokens or legally shareable token hashes, tokenized prompt length, arrival timestamp, sampling settings, max completion tokens, model/tier, SLO class, input provenance, deterministic seed if applicable.

`EngineStateSnapshot`: captured-at timestamp, worker ID, engine version/commit, epoch (when implemented), active/waiting requests, running/waiting counts, admission-relevant KV metrics, scheduler budget, prefix caching observables (reported vs inferred), GPU state metadata; each field tagged `observed|estimated|missing` and measured freshness. A prometheus scrape does not establish atomic capacity.

`ReplaySpec`: exact input prefix hash, candidate request ID, intervention worker ID or `OMIT`, baseline/intervention arm order, RNG seeds, snapshot fingerprint, common H, warm/cold-cache policy, physical boundary ID, engine/model/checkpoint hashes, measurement device identity, run index, failure reason.

`EnergyMeasurement`: physical boundary (`PDU_AC_CLUSTER` preferred; `NVML_GPU_BOARDS` secondary, `NVML_RAPL_SUBSYSTEM` explicitly bounded), units joules, start/end timestamps, raw counter samples, missing-data flags, source, uncertainty, and `measured|simulated` status.

`CounterfactualPair`: baseline run ID and intervention run ID; matching initial fingerprint and boundary; measured `delta_E = E_admit - E_omit`; variation over repeated pairs; state-match and clock-drift diagnostics; admission result (accepted vs rejected, not 'high energy').

`TrainingExample`: only pre-admission features, source pair IDs, measured label, grouped train/validation/test split ID, no future-step or post-treatment leakage.

## Online safety contracts

`EngineAdapter`: `observe_state()`, `can_attempt_admission()` (advisory; may be unavailable), `attempt_admission()` (native decision via checked integration), `measure_engine_overhead()`, `list_caps()`. Implement honest `MockEngineAdapter` first. Engine-side capacity/actual scheduler behavior is final authority; a gateway cannot declare success solely from a locally stored counter.

`Scorer`: `(request, candidate_state)->(delta_energy_hat_J, uncertainty_J, source_model_version)` with missing-feature policy. Signed cost; never clip negative predictions to zero automatically.

`LatencyRiskModel`: `(request, state)->(estimated_P_TTFT_violation, estimated_P_TPOT_violation, calibration_metadata)`. Predicted SLO-feasibility is not a theorem. Collect measured TTFT and TPOT even if model unavailable.

`Decision`: candidate set, rejected/stale features, each score and policy constraint, selected attempt, native admission result, retry count, queue/defer/reject, timestamp, local overhead and seed.

Do not invent an existing vLLM gateway-level `try_admit(expected_epoch=...)` API. Code must pin a specific vLLM commit and **prove** adapter behavior against its native scheduler or document the required engine patch. vLLM V1 uses a unified scheduler and a KVCacheManager with `allocate_slots`; it is not a public distributed transaction API.

## Theorems and their limitations

1. Signed energy difference is exact **only** for matched physical boundaries/horizons; measured counters and replay matching remain empirical.
2. Shapley ex-post allocation is not generally ex-ante marginal dispatch; toy rank reversal is not real-world savings.
3. `J(selected)-J(best) <= 2*epsilon` assumes identical true feasible sets and uniform errors `<=epsilon` for every candidate; do not present as unconditional.
4. Atomic capacity invariant assumes allocator checks + reservations atomically and actual usage stays within reserved blocks; not proved for unmodified serving engine.
5. Optional Bernoulli audit confidence is retrospective comparative-error estimation, not an automatic factual safety gate.

## First-stage limits
One model/quality tier, two same-class replicas where available, locally repeatable recorded traces, fixed model/checkpoint; no carbon, DVFS, disaggregation, semantic cache, HRL or advanced conformal controller. Data ingestion and CPU-only tests can start without GPUs.
