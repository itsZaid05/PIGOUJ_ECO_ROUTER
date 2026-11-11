# Experimental protocol — only execute after prior gates

## Causal treatment and labels

Main offline label: for the **same reconstructed prefix state**, use baseline arm that omits the candidate and intervention arm that admits it to worker `w` at time `t`. No subsequent arrivals for the primary isolated busy-period estimand. `label_J = E_admit_w - E_omit`; compare all workers against the same omit arm where feasible, accounting for pairing/repeated runs. Fixed common horizon `H` must cover both executions or the pair must be invalidated/censored by a pre-specified rule. Include end-of-horizon idle and startup as defined by the common boundary; identical idle cancels in paired difference but still exists in measured totals.

Do not claim a single CUDA context was cloned, or that deterministic sampling guarantees identical outputs; reconstruct by repeated prefix replay, record state fingerprints and divergent generations. Disaggregated servers, multiple model tiers and background workloads are **out of scope** for primary test.

## Trace/capture standard
- Request ID and session, offered arrival, tokenized prompt, sampler options, max output length, runtime/model/hash, per-request seed, sequence of emitted output token count/timing, finish reason, SLO class.
- Trace provenance and permission; never capture private raw user prompts without consent. Default public/synthetic benchmark traces.
- Worker state before arrival: running/waiting counts, actual KV free/allocated block statistics if exposed, queued tokens, prefix-hit observables, preemption, running GPU power, clock/temperature and stale flags.
- Every run: environment, experiment arm, seed, start/end wall clocks, meter IDs, energy boundary, watt/counter sample series, thermal start/finish and model/engine commit hash.

## Measurement first
Preferred primary endpoint: **cluster AC PDU joules per 1,000 SLO-compliant output tokens** for equal offered workload. Secondary: NVML GPU board energy and optional verified non-overlapping RAPL component sum. If PDU unavailable, change the claim to the measured subsystem: do not describe it as whole-node energy. Capture absolute J and completed/rejected rates to detect degenerate reject-everything optimization.

## Prediction evaluation
- Train direct delta model on physical paired replay data; optionally compare with event-power explanatory surrogate.
- Targets: delta_J, sign/rank correctness, *decision regret against paired measured oracle*, error versus KV pressure, cache hits, concurrency and OOD traces.
- Split by trace/session. Record training trace IDs and preprocessing hashes. Compare regression-only and rank-loss alternatives.

## Routing comparisons
Same serving engine, model weights, sampling policy, offered arrival traces, hardware, quality/SLO definitions and measurement boundary for all policies. Prespecified: random/round robin, shortest queue, prefix affinity, prefix+queue, phase-aware power heuristic. For heterogeneous extension only, compare PEARL/input-only energy and quality-matched baselines. Shapley/JCalib = diagnostic when it is only ex-post accounting; do not assert an online routing implementation exists.

## Statistical plan
Paired independent offered traces/seeds; randomized policy order; A/A controls. Pilot estimates paired treatment-difference variance. Prespecify and freeze confirmatory fresh-seed sample size, primary effect (log ratio or paired relative difference), confidence intervals, noninferiority SLO/rejection margins, multiplicity. Wilcoxon ties/zeros may invalidate naive `method='exact'` claims. Report raw and robust sensitivity analyses, not only p-values.
