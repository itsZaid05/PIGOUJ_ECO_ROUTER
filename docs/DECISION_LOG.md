# Decisions and verification ledger

| Date | Decision | Evidence / assumption | Current status |
|---|---|---|---|
| 2026-11-11 | v7 is canonical, earlier designs are historical | Independent research synthesis and prior failure audits | Architecture candidate |
| 2026-11-11 | Offline physical paired-replay labels replace production four-stage symbolic GPU model | Engine scheduling and cache semantics too complex for hand-built exact model | Proposed, unimplemented |
| 2026-11-11 | Native engine admission is authoritative | Gateway KV shadow is non-atomic and stale | Contract defined; integration not verified |
| 2026-11-11 | First test uses homogeneous replicas | Removes model-quality confound | Planned |
| 2026-11-11 | Reference math suite has 8 passed checks | `reference/PIGOUJ_test_results.txt` | Verified toy/math only |
| 2026-11-11 | No measured energy result exists yet | No GPU experiment / raw hardware data | Unverified |

**Codex must append new rows after every phase with git commit and test/log references.**

## Phase 0 and CPU Phase 1 — 2026-11-11

Archive imported into a new local Git repository at
`b7acf7bfb610ffd0f52d1c227acc53d403ffd333`; no source repository/commit was
supplied in the archive. The completed implementation/evidence commit is
identified by local tag **`phase0-1-cpu`** (included in the delivered Git bundle).
This section supersedes the initial "unimplemented" readiness rows for CPU
contracts only. No remote repository was modified.

| Decision | Evidence and assumptions | Status / blocker |
|---|---|---|
| Choose CPU mock on the actual Debian/x86_64 host | `environment_raw.json`; no NVIDIA devices, nvcc, nvidia-smi, NVML or exposed RAPL files | Phase 0 complete; sensor support on a real GPU remains unknown |
| Pin CPU environment separately from GPU dependencies | `pyproject.toml`, `requirements-dev.lock`; Python 3.12.14; `dependencies.log` | CPU setup executable; Python 3.11/macOS not exercised |
| Inspect available vLLM 0.33.0 at source commit `4ba787ec9959e566d3b587a796dff07673324da5` without installing it | `vllm_api_audit.json` and hash-pinned source copies; allocation is internal and enqueue is not reservation | Source-only; no native epoch RPC proven; engine-side instrumentation/semantics still required |
| Use frozen strict Pydantic contracts and exact replay fingerprints | `schemas.py`, `replay.py`, `tests/test_schemas.py`, `tests/test_replay.py` | CPU contracts implemented; exact synthetic equality is not physical state reconstruction |
| Native-authority contract implemented only in the deterministic mock | `engine_adapter.py`, `routing.py`, capacity/staleness/batch/cache property tests | No real engine hooks; virtual slots/times/cache are arbitrary test mechanics |
| Persist explicit synthetic pair demonstrations and an outcome for every offered request | `synthetic_demo/runs.jsonl`, manifests and pair ledger: 2 valid, 4 infeasible, 2 censored pairs; 16 arm records | Zero physical measurements; literal false training eligibility; no failed/censored energy labels |
| Keep the canonical sign and full common horizon | `energy.py`, `validation.py`; negative-delta and altered-boundary/timestamp/prefix tests | Software checks only; physical idle, overhead, clocks and drain fidelity untested |
| Use small exclusive JSONL evidence rather than add Parquet dependencies now | Frozen typed records, exclusive file creation, committed hashes | Physical Parquet capture deferred until a verified meter/engine path exists |
| Run actual implementation/property tests separately from toy reference checks | `commands.json`: 66 implementation tests; 8 reference math checks; lint/format/type/dependency checks all exit 0 | CPU Gate A passes; reference proofs do not validate GPU behavior |
| Block physical pair validation in this implementation | `physical_pending.log`, `tests/test_replay.py`; physical preflight exits 2 intentionally | Gate B / physical Phase 2 NO-GO; next steps in `PENDING_TESTS.md` |

Artifact paths above are relative to `artifacts/validation/` unless they name
source/config/test files. Exact commands, raw outputs, exits, JUnit and validated
source hashes are retained. No physical energy gain, learned model, native
scheduler patch, paid job or UI was produced. Historical research sources and
reference test code remain unchanged.

## Final Gate A re-audit / Phase 2 preparation — 2026-11-11

Base: `e7b362c0da44c1b3867f8e46f021994704552e13` / `phase0-1-cpu`.
Follow-up commit is identified by local tag `gate-a-final-cpu`. The user supplied
`https://github.com/itsZaid05/PIGOUJ_ECO_ROUTER` after authorizing a new repo/push;
it was empty, public and writable when inspected. Publication is within that
explicit request; this is not physical-experiment authorization.

| Decision | Evidence | Status / limits |
|---|---|---|
| Independently rerun the unchanged baseline before edits | `artifacts/validation/gate-a-final/baseline/`: 66 implementation tests, 8 reference checks and existing checks pass | Original evidence preserved |
| Add negative assertions rather than rely on the prior checklist | `pre_fix_regressions.log`: 15 failures / 10 passes in newly added cases before fixes | Reproduced wrong-worker/future-arrival, duplicate/unknown/missing/stale state and impossible output timing gaps |
| Reject wrong-worker attempts before side effects; require consistent current mock state and completed-output window | `engine_adapter.py`, `routing.py`, `schemas.py`, `validation.py`; new audit regressions | Mock-only guarantees; no native reservation invented |
| Preserve original fixture verdicts and canonical negative/zero/positive labels | `test_committed_baseline_pair_verdicts_remain_unchanged` and signed/censored/missing-energy pair tests | All 8 original pair verdicts match; physical labels stay blocked |
| Add read-only telemetry with explicit C ABI and UUID selection | `telemetry.py`, `probe_physical_capabilities.py`, `test_telemetry.py` | CPU stubs tagged test_fixture; actual NVML ABI/sensor branches still unverified on hardware |
| Prepare exclusive-output Stage 0 capture without model/CUDA execution | `phase2_stage0.py`, `test_stage0.py`, `phase2-prep/cpu-stage0/stage0.json` | CPU negative path exit 2; no UUID means no device sampling |
| Refine native mapping to include real frontend queue admission | Exact source review: AsyncLLM.check_admission vs scheduler allocate_slots/None, queue/preemption/prefix events; `native_source_map.json` | Frontend HTTP 503 is distinct from KV deferral; no expected_epoch RPC established |
| Resolve a separate hashed GPU environment candidate | 200-package Python 3.12/manylinux_2_39 lock; 2.28 attempt failed for llguidance wheel compatibility | Metadata only; no GPU stack installed, no driver/model fit claim |
| Accept CPU Gate A, retain physical Gate B stop | `gate-a-final/final/commands.json`: 106 tests, 8 reference checks, lint/format/types/dependency checks pass | University allocation, installed build/native adapter, approved model and calibrated meters still missing |

The native patch, native integration suite, physical meter calibration, replay
matching tolerance and substantial hardware workloads remain future work. No
physical energy readings, training labels, trained model or savings were
produced. Canonical/historical research sources and reference math code remain
unchanged. Detailed remaining dependencies and the first GPU command are in
`GPU_ACCESS_REQUIREMENTS.md` and `PHASE2_EXECUTION_PLAN.md`.
