# Final audit of CPU Gate A — PIGOU-J v7

Date: 11 November 2026. Reviewed base: **e7b362c** / **phase0-1-cpu**.
The follow-up implementation/evidence is identified by Git tag
**gate-a-final-cpu**. This is a fresh code/contract review and execution against
the base, not an external institutional review or a GPU experiment.

**Decision: CPU Gate A PASS after fixes. Physical Gate B remains NO-GO.**

## Audit method and reproduced weaknesses

Read all CPU modules and their tests against `VALIDATION_GATES.md` and the v7
architecture contracts. Before editing, reran the full unchanged gate into
`artifacts/validation/gate-a-final/baseline/`: **66 implementation tests**, all
8 reference math checks and the original lint/type/dependency checks passed.

Then added 25 independent negative/sign/admission cases. Before fixes, **15
failed and 10 passed**; raw historical failure output and command/exit metadata
are saved as `pre_fix_regressions.log` / `pre_fix_regressions_command.json` in
`artifacts/validation/gate-a-final/`. These failures are not hidden by the old
checklist. The final suite includes those cases plus original-fixture
compatibility and telemetry/Stage 0 tests.

| Finding | Before | Fix and verification |
|---|---|---|
| Wrong-worker snapshot | An epoch from another worker could authorize a mock attempt because only its integer epoch was forwarded. | Adapter protocol exposes worker identity; `attempt_once` checks identity before native/mock side effects. Regression checks target snapshot remains unchanged. |
| Request offered in the future | Mock could accept before request arrival, potentially creating inconsistent timing. | Validate arrival against current mock time before any admission mutation. |
| Duplicate/contradictory snapshot membership | Duplicate active/waiting/cache entries and active/waiting overlap were constructible. | Schema now rejects those conditions. Queue ordering is preserved. |
| Equal missing or old core state | Both arms could report identical missing/old core fields, recompute hashes, and obtain a label. | CPU pair verifier requires present, current active/waiting/KV/budget/cache state; GPU metadata remains explicitly missing in CPU mode. Physical freshness/tolerance is not inferred from this rule. |
| Unoffered active state | Hash equality did not prove that active IDs came from the offered prefix. | Verify active/waiting IDs and active token caps against the immutable prefix. |
| Impossible completed-output window | A completion beyond the recorded drain/horizon could still be labelled. | Verify completion timing against the recorded common window and drain. This uses exact synthetic ticks/TPOT; physical integration still needs real token timestamps. |
| Weak energy failure coverage | Most bad counters were tested only in the energy helper. | Full pair tests now require invalid/no delta for missing flags, absent/null samples, resets and reversed sample times. |
| Narrow signed/admission assertions | Negative sign and happy path existed; actual rejection and zero-label assertions were limited. | Test negative, zero, positive differences; real mock capacity/stale rejection reasons; missing service values; unchanged eight committed baseline pair verdicts. |

## Gate A traceability

| Acceptance item | Evidence and scope |
|---|---|
| Real modules are tested | Pytest imports package implementations; Hypothesis generates admission sequences and paired seed/order inputs. Tests are not copies of the reference formulas. |
| Stale epoch / authoritative admission | Mock compares current epoch before capacity decisions; stale and capacity rejections preserve allocation/epoch state. Advisory positive advice cannot force acceptance. `routing.attempt_once` performs no alternative force-dispatch path. Worker identity is now checked too. |
| Immutable offered records | Frozen strict request/sampling/trace/manifest/outcome models contain tuples/frozen children, stable content hashes and validated JSON round trips. Mutation attempts on nested records fail. Caller-supplied lists/unknown fields are rejected where strict tuples/contracts require it. This is not signing, and deliberate low-level object or file mutation is outside the immutability claim. |
| Invalid/censored/missing-energy exclusion | Pair verifier checks common start/H, drain flags, actual offered content/hashes, identity metadata, boundaries/meters, endpoints and monotonic counters. Invalid, infeasible and censored outcomes have null delta. Tests exercise the pair path, not just the helper. |
| Replay state fingerprints | Exact hashes cover relative timestamp, identities, epoch, ordered active/waiting state, cache/budget/KV observations, sources/freshness and GPU metadata. Present/current core state and prefix membership are required in CPU mode. GPU identity/clock/temperature may be missing in CPU mode; physical records are explicitly refused. No physical matching tolerance or reconstruction fidelity is claimed. |
| Signed labels / units / provenance | Label is `E_admit - E_omit`, preserves negative/zero/positive values, units J, pair/repeat/seed/order metadata and `synthetic_demonstration` evidence. `eligible_for_physical_training` is literal false. |
| Offered traffic and outcomes | Every prefix request and candidate has exactly one recorded outcome. Baseline explicitly omits candidate without admitting it. Intervention records mock acceptance/rejection. One-token TPOT is null; rejected/omitted service measurements are missing, not zero. |
| Separate reference evidence | All 8 original toy/math checks pass separately; their code is unchanged. They establish neither native engine behavior nor physical energy gains. |

The original 16 arm records / 8 pair ledger entries remain byte-for-byte
unchanged. A regression loads and revalidates all eight original verdicts with
the strengthened implementation. New demonstration records are saved separately
under `gate-a-final/final/synthetic_demo/`.

## Exact final verification commands and outputs

Executed from repository root using the existing CPU `.venv`:
`.venv/bin/python scripts/validate_cpu.py --output artifacts/validation/gate-a-final/final`
(exit 0). Exact argv, exits, raw-output SHA-256 hashes and logs are saved in
`artifacts/validation/gate-a-final/final/commands.json`; JUnit and validated
source/config hashes are retained alongside it.

### reference

```bash
.venv/bin/python reference/PIGOUJ_math_checks.py -v
```

Exit 0; log `artifacts/validation/gate-a-final/final/reference.log`.

```text
test_atomic_reserved_block_invariant (__main__.TestMath.test_atomic_reserved_block_invariant) ... ok
test_equal_common_horizon_energy_idle_cancels (__main__.TestMath.test_equal_common_horizon_energy_idle_cancels) ... ok
test_marginal_energy_can_be_negative (__main__.TestMath.test_marginal_energy_can_be_negative) ... ok
test_shapley_equal_marginal_for_additive_coalition (__main__.TestMath.test_shapley_equal_marginal_for_additive_coalition) ... ok
test_shapley_wakeup_rank_reversal (__main__.TestMath.test_shapley_wakeup_rank_reversal) ... ok
test_signed_bilinear_energy_identity (__main__.TestMath.test_signed_bilinear_energy_identity) ... ok
test_unbiased_bernoulli_audit_exact_enumeration (__main__.TestMath.test_unbiased_bernoulli_audit_exact_enumeration) ... ok
test_uniform_error_two_epsilon_regret_bound (__main__.TestMath.test_uniform_error_two_epsilon_regret_bound) ... ok

----------------------------------------------------------------------
Ran 8 tests in 0.081s

OK
```

### unit_tests

```bash
.venv/bin/python -m pytest -q --junitxml=artifacts/validation/gate-a-final/final/junit.xml
```

Exit 0; log `artifacts/validation/gate-a-final/final/unit_tests.log`.

```text
........................................................................ [ 67%]
..................................                                       [100%]
106 passed in 0.99s
```

### lint

```bash
.venv/bin/ruff check src tests scripts
```

Exit 0; log `artifacts/validation/gate-a-final/final/lint.log`.

```text
All checks passed!
```

### format

```bash
.venv/bin/ruff format --check src tests scripts
```

Exit 0; log `artifacts/validation/gate-a-final/final/format.log`.

```text
23 files already formatted
```

### types

```bash
.venv/bin/mypy
```

Exit 0; log `artifacts/validation/gate-a-final/final/types.log`.

```text
Success: no issues found in 18 source files
```

### dependencies

```bash
.venv/bin/python -m pip check
```

Exit 0; log `artifacts/validation/gate-a-final/final/dependencies.log`.

```text
No broken requirements found.
```

### synthetic_demo

```bash
.venv/bin/python -m pigouj.harness --output artifacts/validation/gate-a-final/final/synthetic_demo --repeats 2
```

Exit 0; log `artifacts/validation/gate-a-final/final/synthetic_demo.log`.

```text
{"eligible_for_physical_training": false, "evidence": "synthetic_demonstration", "pairs": 8, "physical_measurements": 0, "statuses": {"censored": 2, "infeasible": 4, "invalid": 0, "valid": 2}}
```

### physical_pending

```bash
.venv/bin/python scripts/probe_physical_capabilities.py
```

Exit 2; log `artifacts/validation/gate-a-final/final/physical_pending.log`.

```text
{
  "physical_gate": "PENDING",
  "eligible_for_physical_training": false,
  "requested_samples": 3,
  "requested_interval_seconds": 0.05,
  "clock_note": "same-process call brackets, not calibrated cross-device clock alignment",
  "energy_unit_conversion": "1 millijoule = 0.001 joule; raw values retained",
  "boundary": "GPU board diagnostic only; not AC/whole-node energy",
  "requested_device_uuids": [],
  "status": "unavailable",
  "error": "no NVML library exposed",
  "evidence": "no_readings",
  "platform": "Linux",
  "vllm_version": null,
  "pending": [
    "native allocator/scheduler events and frontend rejection semantics",
    "engine-consistent freshness; no epoch RPC assumed",
    "declared meter boundary, calibration, aligned clocks and raw event capture",
    "idle/loaded/A-A controls, reproducible replay and instrumentation overhead"
  ]
}
```

**Final totals: 106 implementation tests passed, zero failures/errors/skips;
8 separate reference checks passed; Ruff lint/format, strict mypy and dependency
checks passed.** Ruff covers 23 Python files; mypy checks 18 package/test/imported
Stage 0 files. Scripts outside that mypy import scope are linted but are not
claimed to have strict static coverage. Interpreter tested: Python 3.12.14 on
this Debian/x86_64 CPU host. Other interpreters/OSes are not empirically covered.

The generated demonstration contains 2 valid, 4 infeasible and 2 censored
pairs, with 0 physical measurements. The physical probe's exit 2 is expected
pending capability, not a physical pass.

## Phase 2 preparation performed

- Reviewed the exact pinned vLLM 0.33.0 source commit, plus ten additional source/config/build files. Source hashes, GitHub blob identities and AST method anchors are retained in `artifacts/validation/phase2-prep/`. No imported native engine or patched scheduler was executed.
- Mapped real `AsyncLLM.check_admission` frontend queue/backlog rejection (HTTP 503) separately from scheduler enqueue, native KV allocation, None/defer/preemption, actual scheduling, prefix lookup/cache lifecycle and terminal outcomes. No gateway atomic reservation or expected_epoch RPC was established.
- Prepared a 200-package, hashed Linux/Python 3.12/glibc 2.39 GPU environment candidate. The older 2.28 wheel-only target failed; both attempts and final resolution are retained. Source Docker defaults are CUDA 13.0.3 / Ubuntu 24.04; PyTorch 2.14.0 is pinned by the engine. Installation/driver/ABI compatibility remain untested.
- Refactored the read-only NVML probe to bind C function signatures, preserve raw units/return codes, record energy read time brackets and filter allocated physical UUIDs. CPU stub results are tagged test_fixture and never physical labels. Actual NVML ABI/device/sensor operation is still untested on this host.
- Added exclusive-output Stage 0 inventory and installed-source identity comparison. A CPU negative-path execution recorded absent nvidia-smi/nvcc, no vLLM, no CUDA workload or physical labels, and exit 2. Without a UUID, Stage 0 does not sample devices. Code and tests never start a serving engine.

## Remaining integration dependencies and decision

University access/allocation procedure and GPU UUIDs; actual GPU/driver/MIG/
sharing state; compatible installation or reviewed container; approved immutable
model/tokenizer revision and VRAM fit; real native event/state/result schemas
and adapter; serialized freshness semantics (no invented native epoch); validated
per-group KV/prefix observations and event-drop accounting; meter identity,
permissions, support, boundary/non-overlap and calibrated clock alignment;
idle/loaded/A-A controls, empirical replay tolerance and instrumentation overhead.

The existing AdmissionResult remains mock-only. A future real submission cannot
be relabelled accepted until its actual scheduling/allocation evidence has been
observed; frontend rejection, allocator deferral and censoring need distinct
native schema outcomes. Physical pair validation remains disabled.

**GO:** CPU contract foundation and bounded preparation for university access.
**NO-GO:** Gate B completion, physical paired replay, predictor training or any
claim of measured energy savings. No physical experiment was run.

The first GPU-specific command, in an approved allocated university compute
shell, is:

```bash
nvidia-smi --query-gpu=uuid,name,driver_version,memory.total --format=csv
```

Then follow `GPU_ACCESS_REQUIREMENTS.md` and `PHASE2_EXECUTION_PLAN.md`. Stop at
hardware/access incompatibility; no invented server, credentials, model or meter
is needed to interpret this completed CPU audit.
