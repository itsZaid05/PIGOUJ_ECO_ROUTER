# Hardware and access information to collect at Phase 2

The first CPU-only phase requires none of these answers. Codex should ask for only the missing items that block actual NVIDIA instrumentation.

- **Development machine**: OS, CPU, Python version; whether GPU/CUDA available. A Mac can do CPU-only development.
- **Physical NVIDIA testbed**: number of GPUs; model, memory, GPU UUID, driver/CUDA/toolkit; root/SSH/docker access; exclusive/shared use and run-cost approval.
- **Model**: exact Hugging Face ID and revision, number of active replicas, quantization and serving flags; public/open license and benchmark compatibility.
- **Meter**: NVML total energy counter support, PDU vendor/model and sampling API (if present); whether GPU and CPU energy share a boundary; clock synchronization.
- **Engine**: exact vLLM V1 package/commit and scheduler features; whether adding a controlled engine-side telemetry hook is permitted; ability to restart and replay from clean state.
- **Replays**: publicly shareable prompt traces, per-request input tokens, output policies and SLO definitions; storage limits and repetitions budget.
- **Budget**: maximum GPU-hours and approval before any paid run or engine patch.

No credentials, access tokens, passwords or private addresses should be inserted in research documents or committed.
