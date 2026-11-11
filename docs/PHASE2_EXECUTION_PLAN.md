# Phase 2 execution plan: native engine and telemetry feasibility

**Boundary:** preparation complete; hardware access, installation and native
integration remain pending. Do not turn a passed CPU test, a dependency lock,
an HTTP acknowledgement or an incrementing counter into Gate B acceptance.
The first GPU command is in `GPU_ACCESS_REQUIREMENTS.md` and repeated below.

## Revisions and source evidence

Research baseline: `e7b362c` / `phase0-1-cpu`. Engine candidate: vLLM **0.33.0**,
commit **`4ba787ec9959e566d3b587a796dff07673324da5`**. Five original source files
are hash-pinned in `artifacts/validation/vllm_api_audit.json`; ten additional
source/build/configuration files were fetched at the same commit, verified
against GitHub blob identities, and SHA-256 recorded in
`artifacts/validation/phase2-prep/source_fetch.json`. Upstream Apache license
copies are retained. All observations below are **static source observations**.

Paths/line numbers below refer to that commit, never a floating main branch.

## Native source to adapter mapping

| Contract or event | Pinned source and semantics | Required integration / remaining gap |
|---|---|---|
| Request submission | `vllm/v1/engine/async_llm.py:add_request` (397); scheduler `add_request` (2931) enqueues and optionally records QUEUED | Record submission/queue acknowledgement independently of physical allocation. Preserve immutable offered descriptors and request IDs before enqueue. |
| Frontend admission rejection | `AsyncLLM.check_admission` (325), called during request addition (551,578); queue-count/backlog thresholds raise `QueueOverflowError` / `MaxQueuedTokensError` | These are actual frontend limits; `vllm/exceptions.py` specifies HTTP 503. Record threshold, rejection reason and offered request. They are not KV allocator rejection or an epoch-checked reservation. |
| Shared queue counters | `vllm/v1/engine/admission_control.py:SharedAdmissionStats` | Counts aggregate unfinished traffic; they do not atomically reserve physical KV for a chosen request. No success inferred from a counter scrape. |
| `observe_state()` | Scheduler `running`, `waiting`, `kv_holding_waiting`, `deferred_waiting`; `get_request_counts`; Request properties `num_output_tokens`, `num_computed_tokens`, statuses | Capture in the serialized scheduler context, retaining request order, blocked reasons, actual generated versus scheduled/computed/in-flight tokens, budgets and queue memberships. Counts alone are insufficient. Avoid double-counting deferred membership that overlaps a queue. |
| Scheduler-step start and budget | `Scheduler.schedule` (699), remaining `token_budget`, `input_budget`, encoder/lookahead budgets | Add versioned step sequence, observation timestamp and configuration hash at a controlled boundary. Existing CPU scalar budget cannot represent every native budget/cache group. |
| Native KV decision | `KVCacheManager.allocate_slots` (380); capacity None at 548 and 588; scheduler running path 914 and waiting path 1435 | Tee the real inputs, return/allocated group IDs and free-block summary. Do not recreate capacity or refcounts in the gateway. Do not call allocation speculatively as a read-only check. |
| Allocation failure and preemption | Waiting path None at 1454 breaks scheduling; running path may preempt and retry (914–982), `_preempt_request` (1799) frees/requeues and may record PREEMPTED | Record `allocation_unavailable` / `deferred` / `preempted`. These are not automatically a terminal admission rejection or an energy label. A pending request at H is censored unless explicit registered rejection semantics apply. |
| Scheduled transition | Waiting queue pop, running append and optional SCHEDULED event at 1547–1572 | This is evidence of actual scheduling for the step, not lifetime full-output reservation. Keep first scheduled event, allocations, step output and later preemptions. Native events require relevant logging enabled; do not assume full detail already exists. |
| Full-input fit flag | `SchedulerConfig.scheduler_reserve_full_isl=True`; allocator `full_sequence_must_fit` uses `min(request.num_tokens, max_model_len)` at 531–548 | It checks the current input/resumed sequence. It is not a hard reservation of all future max_tokens outputs. Preserve native incremental/preemption semantics. |
| Candidate prefix lookup | `KVCacheManager.get_computed_blocks` (266), called through scheduler `_get_local_prefix_cache_hit` (664); returns blocks, computed-token count and shared-prefix boundary | Tee the lookup result actually used by scheduling, including block/cache-group identity, cache-enabled/skip state, hit length and timing. A lookup may emit cache events; don't invoke it as if it were a pure observer. Post-allocation results must not become pre-admission predictor features. |
| Cache lifecycle / fingerprint | `block_pool`, `get_blocks`/`get_block_ids` (732/736), `free` (629), `evict_blocks` (674), `reset_prefix_cache` (683) | Observe native allocation/cache/reset events and meaningful per-group identities. CPU mock cache_epoch is a set-size fixture, not a native cache epoch. Real fingerprint schema and tolerance need empirical validation. |
| Cache event/stat sinks | `take_events` (705) drains events; `make_prefix_cache_stats` (238) resets statistics | Tee the existing event pipeline with one owner rather than introducing a second destructive reader. Include sequence/drop counts and backpressure. `get_num_common_prefix_blocks` (700) is deprecated and returns zeros here; do not use it as prefix affinity. |
| Finish, abort and errors | `update_from_output` (2259), `finish_requests` (2964), `RequestStatus` in `vllm/v1/request.py` (370) | Retain actual stop/length/abort/error outcomes and emitted token timestamps. Never rename an abort, internal error or generation failure as capacity rejection. |
| `can_attempt_admission()` | No checked native KV reservation API established | Return unavailable/None, or explicitly advisory frontend eligibility. Native scheduling remains authoritative. |
| `attempt_admission(... expected_epoch)` | The mock supports it; inspected native interfaces do not expose the assumed RPC | A real submission must initially be `submitted`, with asynchronous scheduled/deferred/rejected evidence. Extend the mock-only result schema before real integration. A native serialized state-sequence/precondition policy, if required, must be separately designed and tested. No synthetic epoch invented from a scrape. |
| `measure_engine_overhead()` and `list_caps()` | No PIGOU-J native implementation exists | Report unsupported capabilities honestly. Measure actual instrumented/uninstrumented CPU latency and in-boundary energy on the host. Mock operation count is dimensionless. |

The existing `AdmissionResult.source` permits only `mock`, and the pair verifier
refuses measured records. That deliberate block remains. A real adapter needs
versioned native event/result/state schemas, including submitted/scheduled/
deferred/frontend-rejected outcomes and per-group KV data, before physical
pair validation can be enabled. No native patch is included in this task.

## Installation candidate — commands for the university host only

First obtain the inputs in `GPU_ACCESS_REQUIREMENTS.md`. Use a fresh checkout
of the audited research commit in an approved allocation. The following
commands have **not** been executed against university hardware.

First GPU command:

```bash
nvidia-smi --query-gpu=uuid,name,driver_version,memory.total --format=csv
```

Record the UUID assigned to this allocation, not merely GPU index 0. Check OS,
libc and Python, and get administrator confirmation that the CUDA 13 candidate
is supported. The successful metadata-resolution target is Python 3.12 / Linux
x86_64 / glibc 2.39. For another target, create a separate lock and record any
change; do not pretend this candidate was tested there.

```bash
python3.12 --version
ldd --version
python3.12 -m venv .venv-gpu
.venv-gpu/bin/python -m pip install --require-hashes -r configs/phase2-linux-py312-cu13.lock
.venv-gpu/bin/python -m pip install --no-deps --no-build-isolation -e .
.venv-gpu/bin/python -m pip check
.venv-gpu/bin/python -m pip freeze --all
```

Save complete installation outputs and the exact installed inventory in the
private evidence directory described below. Do not mix the CPU development
lock into this environment. A wheel install is a reproducible candidate, not a
proof of CUDA binary provenance. Stage 0 compares installed Python source hashes
against the original five inspected files and version; mismatch blocks native
integration. An instrumented build needs a checked-out pinned source tree,
recorded patch/build digest, and an independently verified compiler/CUDA stack.
No source-build/precompiled-wheel shortcut is assumed to work.

## Reproducible Stage 0 capture

These commands inventory capabilities only. The repository is public; actual
university device/job/host metadata should be retained under ignored
`artifacts/raw_private/` and reviewed before sharing. Do not use real private
requests for this probe. Run from repository root and choose a new output
path for every capture. Set PIGOUJ_GPU_UUID to the UUID confirmed for the
allocation, then use the same interpreter/environment being tested.

```bash
export PIGOUJ_GPU_UUID=GPU-REPLACE-WITH-ACTUAL-ALLOCATED-UUID
PYTHONPATH=src python3 scripts/phase2_stage0.py \
  --gpu-uuid "$PIGOUJ_GPU_UUID" \
  --output artifacts/raw_private/stage0-before-install
.venv-gpu/bin/python scripts/phase2_stage0.py \
  --gpu-uuid "$PIGOUJ_GPU_UUID" \
  --output artifacts/raw_private/stage0-after-install
.venv-gpu/bin/python scripts/probe_physical_capabilities.py \
  --gpu-uuid "$PIGOUJ_GPU_UUID" --samples 10 --interval-seconds 0.1
```

`GPU-REPLACE-WITH-ACTUAL-ALLOCATED-UUID` is a visibly invalid placeholder and
must be replaced; no default device identity or model is invented. Stage 0
without a UUID performs inventory and **does not sample NVML**. The probe
filters physical NVML UUIDs; a missing requested UUID remains an explicit
allocation mismatch. No CUDA/model process is started. **Exit 2 is expected
PENDING**, including on a host with working counters. Capture stdout/stderr
and exit status; do not hide errors with `|| true` or label exit 2 a pass.

`stage0.json` includes actual command results, libc/Python/package versions,
allocation metadata, source-hash comparison and telemetry capability results.
Successful NVML samples retain raw cumulative millijoules and instantaneous
milliwatts with return codes and monotonic call brackets plus wall time.
1 mJ = 0.001 J. No-increment over a short interval is inconclusive; reset,
NOT_SUPPORTED, missing data or symbol, initialization failure and unavailable
UUID remain explicit. Power is diagnostic, not a silently integrated fallback.
Neither reading frequency nor a call timestamp establishes meter resolution,
accuracy, integration coverage or clock synchronization. CPU telemetry fixtures
are separately tagged `test_fixture` and never written as hardware evidence.

The CPU-side command was executed once into
`artifacts/validation/phase2-prep/cpu-stage0/`: it recorded absent nvidia-smi /
nvcc, no installed vLLM, skipped NVML without allocation, no CUDA workload,
no training labels and exit 2. This is CPU negative-path evidence only.

## Stage 0 completion and workload stop line

After installing and identifying the real meter, implement the native event
adapter in an isolated checkout. Freeze the schema, enabled event flags,
configuration, model/tokenizer hashes, drop policy and clock mapping. Run the
following **pending** integration matrix only after hardware/allocation and
substantial-use authorization exist:

| Pending check | Evidence required to pass |
|---|---|
| Empty native engine | Coherent empty queues, actual groups/budget/UUID/version and no fabricated values. |
| Accepted finite request and one-token output | Frontend submission, first native schedule/allocation, token delivery/finish event; TPOT undefined for one token. |
| Queue cap and allocator pressure separately | Real frontend 503 reasons versus native None/defer/preempt events; no forced dispatch or false reservation. |
| Fresh/stale native state sequence | A registered serialized observation policy and a controlled state change; fail/defer safely rather than silently accept stale assumptions. |
| Prefix cold/warm/reset | Actual lookup and group/block events, reset success/failure, complete loss/drop accounting; no gateway cache mirror assertions. |
| Idle/loaded meter and A/A reconstruction | Raw sensor trace, native/event clock mapping, equivalent reconstructed state, registered tolerance, drift/noise and overhead estimates. |
| Boundary accounting | Same declared devices, full common H and idle tail, in-boundary gateway/audit overhead; NVML GPU board totals cannot support whole-node claims. |

No executable native-engine integration suite exists yet; the table is a
pending implementation/measurement plan, not fabricated commands or skipped
passing tests. Model smoke tests require the still-missing approved checkpoint
and native event path, so this task stops before them.

**Gate B remains NO-GO** until this matrix has real evidence. Physical paired
replay (Phase 3), physical-label ingestion, model training, energy savings and
an online router remain blocked. A working read-only preflight permits further
bounded integration work, not the later experiments.
