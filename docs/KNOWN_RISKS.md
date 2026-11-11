# Risks, uncertainties, and scientific failure modes

| Risk | Why it matters | Mitigation / test |
|---|---|---|
| Counterfactual physical state cannot be snapshotted | Same prefix may generate different KV and scheduling state | Replay entire history, state fingerprints, paired randomization, reject invalid pairs |
| Local fixed-horizon delta differs from live global effect | Future arrivals change every routing decision | Limit primary claim to local decisions; separately test matched future arrivals and live policy outcomes |
| Incremental-energy differences smaller than noise | Learned rankings can be dominated by sensor drift | A/A controls, many paired repeats, significance/CI of sign and decision regret |
| Wrong physical boundary | GPU-only savings may mask PSU/host losses | Prefer PDU; otherwise narrow claim and report NVML/RAPL only |
| vLLM internal APIs change | The proposed atomic admission contract may not exist | Pin commit; inspect actual allocator and scheduler; adapter fail-closed, document required engine instrumentation |
| Prefix-cache hit not independently observable at gateway | Synthetic cache-affinity signals may be inaccurate | Use engine-origin telemetry where possible; stale/unavailable => missing feature or fallback |
| End-to-end energy win just rejects hard requests | Ratio might improve while service degrades | Always compare offered volume, completion/rejection, SLO and goodput |
| Data leakage across train/test from same prefixes | Inflated prediction/ranking accuracy | Group splits by trace/session; pre-admission features only |
| Different sampled outputs across arms | Counterfactual energy confounded by output length | Fix controlled lengths where possible; log divergence and natural-EOS sensitivity |
| Robust intervals not shift-robust | Offline calibration can fail in traffic bursts | Coverage diagnostics by load/cache regime, OOD fallback, no distribution-free claim |
| Only toy tests pass | No physical correctness established | Distinct test categories and evidence ledger; move to GPU only with approved gate |
| Quality tiers create extra causal confounding | Different answers, output lengths, and audit costs | Homogeneous one-model study first, heterogeneity separate |
