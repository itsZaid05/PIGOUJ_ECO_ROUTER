# PIGOU-J v7: Phase 0 and CPU Phase 1 completion report

Completed in the extracted repository on 11 November 2026. The source baseline
is local commit `b7acf7bfb610ffd0f52d1c227acc53d403ffd333`; the implementation
and evidence are recorded at local Git tag `phase0-1-cpu`. No remote was used.

**CPU Gate A: PASS. Next physical Phase 2: NO-GO on this host.**

## Files added or changed

Added:

- `pyproject.toml`, `requirements-dev.lock`: package/build configuration, pinned CPU dependencies, pytest/Ruff/strict mypy settings.
- `src/pigouj/__init__.py`, `py.typed`, `schemas.py`, `engine_adapter.py`, `replay.py`, `energy.py`, `routing.py`, `validation.py`, `harness.py`.
- `tests/__init__.py`, `conftest.py`, `test_schemas.py`, `test_engine.py`, `test_energy.py`, `test_replay.py`.
- `scripts/audit_environment.py`, `inspect_vllm_source.py`, `probe_physical_capabilities.py`, `validate_cpu.py`.
- `docs/ENVIRONMENT_AUDIT.md`, `PENDING_TESTS.md`, this report.
- `artifacts/validation/`: raw host/API evidence, pinned upstream source copies and license, exact command outputs/exit metadata, JUnit, source hashes, full changed-file inventory, and 16 synthetic arm records plus manifests and pair ledger.

Changed: `.gitignore`, `README.md`, `docs/DECISION_LOG.md`,
`docs/PHASE_PLAN.md`, `docs/VALIDATION_GATES.md`.

The full per-file inventory is `artifacts/validation/changed_files.txt`.
Canonical research files, historical PDFs, and existing reference test sources
are unchanged from the imported baseline.

## Exact verification commands and results

Commands ran from the extracted repository root, using its local `.venv`.
The acceptance wrapper was `.venv/bin/python scripts/validate_cpu.py` (exit 0).
For each subprocess it retained argv, exit code, output hash and raw output in
`artifacts/validation/commands.json` and the named logs. Its expected physical
probe exit 2 is a pending result, never an integration pass.

### reference

```bash
.venv/bin/python reference/PIGOUJ_math_checks.py -v
```

Exit: 0. Raw output: `artifacts/validation/reference.log`.

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
Ran 8 tests in 0.097s

OK
```

### unit_tests

```bash
.venv/bin/python -m pytest -q --junitxml=artifacts/validation/junit.xml
```

Exit: 0. Raw output: `artifacts/validation/unit_tests.log`.

```text
..................................................................       [100%]
66 passed in 0.88s
```

### lint

```bash
.venv/bin/ruff check src tests scripts
```

Exit: 0. Raw output: `artifacts/validation/lint.log`.

```text
All checks passed!
```

### format

```bash
.venv/bin/ruff format --check src tests scripts
```

Exit: 0. Raw output: `artifacts/validation/format.log`.

```text
18 files already formatted
```

### types

```bash
.venv/bin/mypy
```

Exit: 0. Raw output: `artifacts/validation/types.log`.

```text
Success: no issues found in 14 source files
```

### dependencies

```bash
.venv/bin/python -m pip check
```

Exit: 0. Raw output: `artifacts/validation/dependencies.log`.

```text
No broken requirements found.
```

### synthetic_demo

```bash
.venv/bin/python -m pigouj.harness --output artifacts/validation/synthetic_demo --repeats 2
```

Exit: 0. Raw output: `artifacts/validation/synthetic_demo.log`.

```text
{"eligible_for_physical_training": false, "evidence": "synthetic_demonstration", "pairs": 8, "physical_measurements": 0, "statuses": {"censored": 2, "infeasible": 4, "invalid": 0, "valid": 2}}
```

### physical_pending

```bash
.venv/bin/python scripts/probe_physical_capabilities.py
```

Exit: 2. Raw output: `artifacts/validation/physical_pending.log`.

```text
{
  "platform": "Linux",
  "physical_gate": "PENDING",
  "vllm_version": null,
  "nvml_library": null,
  "nvml_probe": "UNAVAILABLE: no NVML library exposed",
  "pending": [
    "native allocator/admission events and rejected-allocation behavior",
    "engine-consistent freshness/epoch semantics; no remote API assumed",
    "PDU or verified subsystem boundary and calibrated clock alignment",
    "idle/loaded meter repeatability, A/A replay and instrumentation overhead"
  ]
}
```

The reference suite is **8 toy/math checks**, kept separate from **66 actual
implementation tests** (including deterministic Hypothesis properties). Strict
mypy covers the package and tests, 14 source files; Ruff checks the package,
tests and audit/validation scripts, 18 Python files. Vendor snapshots and
historical reference code are not silently folded into these checks. JUnit
reports zero failures/errors/skips. Python 3.12.14 is the tested interpreter;
Python 3.11 and macOS are not tested.

## Demonstrated guarantees

- Strict runtime validation, frozen nested records/tuples and stable content hashes for immutable requests, traces and run manifests; JSON round trips retain contract values. This is immutability and content identity, not cryptographic signing or protection against deliberate low-level object/file mutation.
- Identical offered-prefix content/hashes, candidate descriptors, initial snapshots, model/engine/config identities, meter boundaries, common relative start/horizon, repeat IDs, per-request seeds, workload seeds and reproducible randomized execution order are checked before a label is emitted.
- The verifier checks actual record content against manifest hashes. Tests deliberately alter prefixes, timestamps, caches/fingerprints, hashes, boundaries, windows, outcomes and metadata; mismatches yield invalid ledgers without a delta.
- Omit and admit are distinct actions. Baseline has no candidate admission and records an explicit omission. Intervention requires an admission outcome tied to its candidate and worker. Mock capacity/staleness failures cannot be forced into success by the gateway helper.
- Every offered prefix request and candidate appears in the outcome ledger; missing/duplicate outcomes are rejected. Failed admissions are infeasible, unfinished horizons are censored, and neither receives an energy label. Missing tokens/readings are not silently turned into zero values. One-token TPOT is null.
- Counter windows require endpoints, strictly increasing times, monotone non-missing cumulative counters, joule units and consistent provenance/boundary. The difference is always `E_admit - E_omit`; negative synthetic differences remain signed.
- Demonstrations use repeated prefix reconstruction with independent mock instances and no subsequent arrivals. No CUDA/process snapshot is involved. The committed harness output contains 8 synthetic pairs: 2 valid, 4 infeasible (capacity/staleness), 2 censored. Physical measurements: **0**. All pair records have literal false physical-training eligibility; the Phase 1 verifier explicitly refuses physical records.

## Assumptions and unverified capabilities

The mock is single-threaded. Its capacity slots, cache sets, generation lengths,
completion ticks, timing interference and arbitrary counters are test mechanics,
not vLLM behavior or a physical energy predictor. Matching synthetic seeds and
fingerprints does not establish reproducible GPU kernels, identical physical
initial conditions, cache hits, real batch interference, energy uncertainty,
SLO compliance or production concurrency safety. JSONL is sufficient for this
small immutable demonstration set; physical Parquet capture remains deferred.

The audited host is Debian 13/x86_64 with 3 exposed virtual CPUs and no exposed
NVIDIA devices, CUDA compiler, nvidia-smi, NVML or RAPL files. No PDU/model
checkpoint was supplied; GPU identity and energy support remain unavailable.
The executable read-only preflight and pending test recipes are in
`docs/PENDING_TESTS.md`.

Installed vLLM: **none**. Available release inspected: **0.33.0**, official
source commit **4ba787ec9959e566d3b587a796dff07673324da5**. Five source files and
their hashes are saved. Internal `allocate_slots` may return None, and scheduler
capacity deferral is distinct from request rejection. `add_request` queues work;
it does not prove a reservation. `full_sequence_must_fit` is not proof that every
possible output token was reserved. No epoch-checked remote admission API was
established. This source check does not replace execution of the pinned engine.

No real adapter, native scheduler patch, physical telemetry collection,
calibrated state/clock matching, A/A replay, physical labels, trained predictor,
measured energy gain, costly GPU job or UI was produced.

## Next-phase decision

**NO-GO for physical Phase 2 execution in this environment.** The prerequisites
are a supported Linux/NVIDIA testbed, installed and revision-verified engine and
model, observed native scheduling/allocation outcomes, and an identified working
meter with a declared boundary. Phase 2 must empirically verify those capabilities
and instrumentation overhead before physical paired replay or training. The
read-only source/preflight work can continue on a suitable host; this report
neither provisions paid compute nor authorizes a later experiment.
