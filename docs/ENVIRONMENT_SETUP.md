# Environment prerequisites and setup commands

## Local CPU-only development (macOS or Linux)

```bash
# From extracted repository root
python3 --version
git --version
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python reference/PIGOUJ_math_checks.py -v
# Codex should then create pyproject.toml and a test/lint environment in Phase 1.
```

The **reference** script uses Python standard library. A machine without NVIDIA CUDA and NVML can build schemas, mock adapters, unit/property tests, paired-replay manifests, and data analysis code, but cannot measure NVIDIA GPU joules. Apple Silicon acceleration through Metal is not equivalent to NVIDIA NVML instrumentation. Do not substitute a Mac CPU/Metal energy sample for target NVIDIA GPU measurement.

## Linux/NVIDIA physical phase — verify, do not assume

```bash
uname -a
nvidia-smi -L
nvidia-smi --query-gpu=uuid,name,driver_version,memory.total --format=csv
python3 --version
# if vLLM exists, inspect exact installed version and source commit
python3 -c 'import importlib.metadata as m; print(m.version("vllm"))' || true
```

NVML `nvmlDeviceGetTotalEnergyConsumption` reports millijoules since driver reload **when supported**. It can return NOT_SUPPORTED. Confirm sensor support and counter precision experimentally. Do not assume all drivers update counters every 50 ms or that 50 ms sampling is a real GPU power sample.

Pin **specific** vLLM V1 source revision and model revision only after the engine-capability audit; do not pin a guessed version from this document. Some current vLLM `KVCacheManager.allocate_slots` code supports `full_sequence_must_fit`, but it is internal scheduler logic; it is not proof that a remote `try_admit` endpoint exists.

## Credentials / paid GPUs
Never commit tokens, private model credentials, GPU-provider SSH keys, IPs, or personal prompt traces. Prefer environment variables. Obtain explicit user approval before provisioning paid compute, running long loads or applying engine patches on shared hosts.
