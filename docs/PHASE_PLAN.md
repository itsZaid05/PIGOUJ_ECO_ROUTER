# Research engineering phases and stop/go criteria

**Execute in order. A phase is completed only when its measured/test artifacts exist.** All CPU-only phases can be done on Mac/Linux; GPU-required phases need real hardware.

| Phase | Scope | Required deliverable | Stop/GO gate |
|---|---|---|---|
| 0 — Environment and specs | Inspect machine/repo, pin toolchain, read v7, reject unsupported API assumptions | `ENVIRONMENT_AUDIT.md`, dependency pins, repo/test workflow, decision log | Environment capabilities honest; tests run |
| 1 — Contract foundation | Typed requests, immutable traces, snapshots, physical boundary, mock engine, pair verifier | Python package, CPU mock + real unit/property tests, logs | No mismatched pairs silently accepted; all actual tests pass |
| 2 — Real engine and meters | Pin vLLM V1 commit and model hash, instrument scheduler/KV-admission events and NVML/PDU | Linux/NVIDIA integration probe, event schemas, sensor trace, instrumentation overhead | Admission and meter signals empirically verified; no forced dispatch |
| 3 — Paired replay | Reconstruct prefix by repeated runs, match fingerprints, omit/admit intervention, same horizon | Physical paired energy Parquet, A/A controls, pair validity ledger, rejected actions | Reproducible enough for ranking; paired noise quantified; physical boundary valid |
| 4 — Learned score | Train direct delta predictor, held-out trace splits, uncertainty and ranking loss ablation | Model card, validation report, MAE, decision regret, rank accuracy | Beating simple heuristics on fresh held-out traces *or falsify* |
| 5 — Online router | Use observed candidate state, robust feasible selection, native accept or safe retry/reject | Service/gateway, failure tests, real telemetry, router overhead | No unsafe admission path; comparisons use same offered traces |
| 6 — Controlled homogeneous pilot | Two/four replicas, 3 load levels and cache regimes, matched baselines | Physical energy, goodput, TTFT/TPOT, rejection, uncertainties, raw logs | Pre-registered practical win without SLO/reject degradation |
| 7 — Confirmatory/generalization | Fresh independent traces and seeds, cross-hardware/model if available | Statistical report and reproducibility archive | Conclusions supported with proper multiplicity and no train/test leakage |
| 8 — Optional quality tiers | Separate capability labels, shadow audits and their energy cost | Measured quality ledger and corrected net energy | No unsupported factual safety claims |

## First three Codex requests

**Initial request:** paste `CODEX_FIRST_PROMPT.md` (Phase 0/1 CPU foundation). **Next:** request Phase 2 only after sharing Linux GPU host details and Phase 1 test outputs. **Then:** request Phase 3 pair replay only after state and meter APIs are verified.

**Do not let Codex skip from a passed mock test to claimed physical readiness.** If physical hardware cannot be reached, work ends with tested CPU code and explicit blocked integration tasks.

## Recorded execution status — 2026-11-11

Phase 0 and the CPU-only part of Phase 1 are complete at local Git tag
`phase0-1-cpu`: measured host audit, pinned CPU toolchain, immutable contracts,
mock-only admission and synthetic pair harness, 66 implementation tests, 8
separate reference math checks, Ruff and strict mypy evidence. See
`docs/CPU_FOUNDATION_REPORT.md` and `artifacts/validation/commands.json`.

Phase 2 physical execution is **NO-GO on this workspace**: no exposed NVIDIA
device/NVML/PDU, installed vLLM or native event/admission adapter. Source-only
inspection of vLLM 0.33.0 is not integration evidence. `docs/PENDING_TESTS.md`
preserves the reproducible preflight and required native/meter tests. No later
phase was executed.
