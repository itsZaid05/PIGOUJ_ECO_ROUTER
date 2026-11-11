# Pending physical integration tests

All items here are **UNTESTED**, and none is counted as a passed unit test. Phase 1's pair verifier explicitly refuses physical records until a real adapter and metering path exist. CPU tests establish software contracts only.

## Reproducible read-only preflight

From a fresh checkout, install the CPU development toolchain as in README. On the intended Linux/NVIDIA host run:

```bash
.venv/bin/python scripts/audit_environment.py > artifacts/validation/gpu_host_audit.json
.venv/bin/python scripts/probe_physical_capabilities.py --gpu-uuid "$PIGOUJ_GPU_UUID"
.venv/bin/python scripts/inspect_vllm_source.py \
  --version 0.33.0 \
  --expected-commit 4ba787ec9959e566d3b587a796dff07673324da5
```

The physical probe launches no model and performs no CUDA workload. Set PIGOUJ_GPU_UUID to the actual allocation UUID first. If NVML exists and an allocation UUID is provided, the probe attempts matching device identity and three cumulative millijoule counter reads, 50 ms apart. Without an allocation UUID, real device sampling is refused. It preserves NVML return codes (including NOT_SUPPORTED) and never substitutes zero for errors. A non-incrementing counter over this short interval is inconclusive. **Exit 2 is always PENDING**, even if counters increment: availability is not calibration or engine integration. This host's captured result is `artifacts/validation/physical_pending.log`: no NVML library and no installed vLLM.

The GPU/NVML branch of that probe cannot be exercised on this host. No portable CPU mock test can establish physical NVML support. The source inspection is rerunnable without a GPU; it verifies downloaded source identity and signatures only.

## Native engine contract to implement and test in Phase 2

The source candidate is vLLM 0.33.0 at commit `4ba787ec9959e566d3b587a796dff07673324da5`. Confirm compatibility on the actual GPU/Python/CUDA stack before treating it as the final serving pin. Record the installed build/source revision, model/checkpoint/tokenizer digests, runtime flags and device UUIDs.

Required instrumentation, currently **not implemented**:

1. Add worker-local observation of scheduler queues and `KVCacheManager.allocate_slots` outcomes, with request IDs, monotonic timestamps, actual cache groups, budget, preemption and allocation events. Distinguish enqueue acknowledgement from scheduled allocation. Do not equate a capacity-related scheduler deferral with a public rejection RPC.
2. Define a consistent freshness/epoch contract at the native scheduling boundary. If an epoch-checked reservation is scientifically required, specify/review an engine-side policy before implementing it. The CPU mock's reservation mechanism is not that patch.
3. Exercise empty worker, known accepted request, capacity pressure, stale observation, actual prefix hit/miss, preemption/chunking and one-token output. Compare emitted events against native scheduler/allocator state. Record safe defer/reject without a fallback that forces dispatch. Thresholds and repeat count must be fixed before collecting acceptance evidence.

There is intentionally no fake native-admission pytest that passes or is skipped behind a simulated device flag. These operations require a real adapter implementation and recorded integration evidence before Gate B can change.

## Meter, clocks and replay

After explicit authorization for substantial GPU use, execute and retain:

| Pending test | Reproducible setup / required observation |
|---|---|
| Sensor identity and support | Enumerate GPU UUID/driver and PDU/sensor identities; preserve counter return codes and raw units. Compare time-separated samples; never infer resolution from polling frequency. |
| Boundary and idle calibration | Declare AC cluster or bounded subsystem devices; prove non-overlap for NVML+RAPL; include in-boundary idle/gateway/audit overhead; fix uncertainty/tolerance using sensor specs and pilot variance. |
| Clock alignment | Record per-run wall/monotonic origin and synchronized meter/event times. H has equal duration and start offset relative to treatment; separate runs have different absolute wall starts. |
| Known load and instrumentation overhead | Collect raw idle/loaded traces and instrumented/uninstrumented comparisons on the same setup. The current mock operation count is neither measured runtime nor measured joules. |
| Prefix reconstruction and A/A controls | Reset and replay identical offered prefixes repeatedly, without CUDA forks; log observed scheduler/KV/cache/thermal fingerprints and generation divergence. Register an empirical matching tolerance instead of silently relaxing exact matching. |
| Physical omit/admit replay | Randomize registered arm order, preserve seed/repeat/model/engine/boundary metadata, freeze future arrivals, drain both arms under common H, retain rejects/censoring and raw readings. No physical label for an infeasible admission. |

No integration test above has been executed, no physical dataset exists, and no predictor training or energy-gain analysis is authorized by this task. Gate B, Phase 3 and training remain NO-GO until the required preceding evidence exists.

The final CPU audit and detailed university installation/native event mapping are
in `GATE_A_FINAL_AUDIT.md`, `GPU_ACCESS_REQUIREMENTS.md` and
`PHASE2_EXECUTION_PLAN.md`. Current probes preserve time brackets, raw units,
return codes and UUID selection; the earlier raw logs remain historical evidence.
