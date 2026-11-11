# Validation and acceptance gates

## Gate A — CPU-only contracts (now)
- [x] `pytest` or `unittest` runs actual modules, not independently retyped formulas.
- [x] Replay pair rejects different prefix hashes, mismatched timestamps, inconsistent energy boundary, differing model/engine hashes, invalid horizon, and missing counter readings.
- [x] Replay labels have canonical sign `E_admit - E_omit`, valid physical units, provenance, repeat ID, and `synthetic|measured` tag.
- [x] Mock engine refuses admission on capacity failure and stale epoch; router does not force a worker.
- [x] Immutable events include all offered requests, service/rejection outcomes and reasons; absent tokens are not silently treated as zero energy.
- [x] Reference 8 toy proofs run and clearly remain separate from implementation tests.

Gate A evidence (2026-11-11, CPU mock only): `artifacts/validation/commands.json`,
`unit_tests.log`, `reference.log`, and `synthetic_demo/`. 66 implementation tests
and 8 separate reference math checks pass. All generated labels are synthetic
demonstrations; the verifier refuses physical pairs in Phase 1. Git tag:
`phase0-1-cpu`. Gate A does not establish physical correctness.

## Gate B — physical instrumentation
- [ ] Running on supported NVIDIA Linux testbed; exact GPU UUID, driver/CUDA/vLLM/model revisions recorded.
- [ ] Native KV and scheduling signals identified and compared with real events; no reliance on scraped metric as atomic reserve.
- [ ] NVML total energy counter works or explicit fallback is documented; any RAPL/PDU sensors listed with *non-overlapping* boundaries.
- [ ] Meters and event clocks aligned; test baseline idle, empty workload, known GPU load, A/A run repeatability.
- [ ] Instrumentation changes measured overhead; no silent dropping of data.

## Gate C — paired counterfactual reference
- [ ] Rebuild same prefix twice without forking CUDA; state fingerprint shows match/mismatch with audited tolerance.
- [ ] Same horizon and physical boundary; admissions rejected by engine marked infeasible, not assigned fictitious energy.
- [ ] Arm order randomized; paired replicates include matching seeds, caches and model; EOS/generation deviations logged.
- [ ] Raw measurements and uncertainty available; cache/wait/active state strata and high-variance failure modes covered.

## Gate D — learned routing and statistical evidence
- [ ] Train/test split by entire trace or session; all online features observed before decision.
- [ ] Holdout MAE, sign accuracy, rank accuracy, expected regret and confidence intervals reported; not only token MAE.
- [ ] Compare against round-robin, shortest queue, prefix affinity, cache+load, phase-aware heuristic, input-only energy methods where applicable.
- [ ] End-to-end energy includes router CPU energy and rejected/held demand; show absolute energy, goodput, SLO pass rate and rejection rate.
- [ ] Fresh confirmatory seeds, locked primary effect/test, tie/zero handling, multiplicity and sensitivity analysis.

## Numerical thresholds
Do not inherit an arbitrary 2% meter error, 4% energy saving or 0.05ms router latency as a physically validated promise. Record plausible design targets *before* the corresponding pilot. Decide tolerance based on sensor specs, variance from the calibration pilot, practical effect size and available runtime; fix thresholds before testing the final comparison.

## Definitive blocker examples
- Model trained on `simulation` records but described as measured.
- Comparing GPU NVML joules for one policy with AC PDU joules for another.
- Counterfactual arms do not match state or common horizon.
- Lack of engine-native admission checks.
- Held/rejected requests removed from denominator/reporting.
- Test cases assert only `score>0` where physical state correctness is the claim.
