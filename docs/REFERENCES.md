# Research sources and critical official integration documentation

## Primary research sources (reviewed in v7 dossier)
1. JouleShare/JCalib — https://arxiv.org/abs/2608.00026
2. TokenPowerBench — https://arxiv.org/abs/2512.03024
3. PEARL — https://doi.org/10.1016/j.future.2025.108218
4. Measured Joules, Learned Routes — https://arxiv.org/abs/2609.23085
5. Festina — https://arxiv.org/abs/2606.30391
6. CacheRoute — https://arxiv.org/abs/2608.19677
7. Beyond Accuracy and Cost — https://arxiv.org/abs/2607.18253
8. Robust Batch-Level Query Routing — https://arxiv.org/abs/2603.26796
9. CEMA-Router — https://arxiv.org/abs/2610.26171

## Official engineering docs checked for the handoff (11 Nov 2026)
- vLLM V1 guide (unified scheduler, chunked prefill, prefix caching): https://github.com/vllm-project/vllm/blob/main/docs/usage/v1_guide.md
- vLLM `KVCacheManager` API (internal `allocate_slots`, `full_sequence_must_fit`, prefix semantics): https://docs.vllm.ai/en/latest/api/vllm/v1/core/kv_cache_manager/
- vLLM metrics: https://github.com/vllm-project/vllm/blob/main/docs/design/metrics.md
- vLLM reproducibility: https://docs.vllm.ai/en/stable/usage/reproducibility/
- NVIDIA NVML total energy counter and NOT_SUPPORTED behavior: https://docs.nvidia.com/deploy/nvml-api/latest/api/group__nvmlDeviceQueries.html
- OpenAI Codex project instructions with `AGENTS.md`: https://learn.chatgpt.com/docs/agent-configuration/agents-md

**Rule:** source links are research guidance, not proof that exact native APIs are present in your pinned checkout. Re-check the installed commit/source before coding engine hooks.
