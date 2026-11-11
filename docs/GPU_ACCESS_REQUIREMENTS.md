# University GPU access requirements

Status: **access not supplied; no physical experiment executed**. CPU Gate A is
reviewed in `GATE_A_FINAL_AUDIT.md`. This document requests the inputs needed to
run the read-only Stage 0 preflight and later implement Gate B. No passwords,
SSH keys, access tokens, private prompts or university host identifiers belong
in this public repository; use the university's approved access mechanism.

## Information to obtain from the university

| Required information | Why it is needed / minimum scope |
|---|---|
| Approved connection/VPN/bastion and scheduler procedure | Use an allocated compute node, not a shared login node, for any CUDA/model work. Obtain the actual partition/account/resource flags from the administrator. None are guessed here. |
| Allocation ID, time allowance, permitted GPU UUID(s) and sharing policy | One GPU is sufficient for native/meter preflight. Two comparable replicas are a later replay/pilot prerequisite, not a Stage 0 prerequisite. Exclusive access or recorded co-tenancy is essential for attributable energy. |
| GPU model, UUID, VRAM, MIG/MPS/vGPU status, driver version | Compatibility and counter availability are empirical. A model name alone does not establish supported NVML energy counters. NVML indices need not match CUDA_VISIBLE_DEVICES indices. |
| OS, architecture, glibc and Python availability | Prepared target is Linux x86_64, Python 3.12, Ubuntu 24.04/glibc 2.39. Other architectures/older libc require a separately resolved environment. |
| Driver compatibility with the chosen CUDA runtime | Pinned source Docker defaults are CUDA 13.0.3 / Ubuntu 24.04 / Python 3.12; resolved PyTorch is 2.14.0 with CUDA-runtime package 13.0.96. Administrator must confirm GPU/driver support against NVIDIA's compatibility documentation. No assumed minimum driver or automatic driver change. |
| Approved venv/container/module policy and storage quota | The GPU stack is large. Use a separate `.venv-gpu`, approved scratch/cache storage, and enough quota for dependency wheels plus one model. No concrete storage requirement can be promised before model selection. Source builds additionally need the supported CUDA toolkit/compiler/build tools. |
| Allowed outbound package/model downloads or an approved mirror | PyPI/files.pythonhosted.org and model/source hosts must be reachable, or the administrator must provide verified offline artifacts. Hashes must match the prepared lock; do not disable TLS checks. |
| One approved model/checkpoint/tokenizer and immutable revisions | Record model/tokenizer digests, license/access permissions, precision, max context and output cap. No model or model hash has been fabricated. VRAM fit must be checked after selecting hardware and model. |
| NVML permissions and energy sensor support | Retain `nvmlInit`, enumeration, UUID and total-energy return codes. NOT_SUPPORTED, missing symbols, inaccessible devices and counter resets remain explicit failures. |
| PDU availability, meter ID, coverage, calibration and clock source | Prefer a whole-cluster AC boundary that includes workers, gateway, idle and audit overhead. Otherwise name the endpoint GPU-board energy or a verified non-overlapping subsystem. A GPU-board counter is not whole-node electricity. |
| Allocation exclusivity, power/clock policy and consent for instrumentation | Do not change clocks, power caps, MIG, drivers or shared engine processes. Instrumentation must be a separate reproducible engine build or reviewed patch, not edits to a shared production install. |

Source compatibility references: the pinned vLLM source and saved metadata under
`artifacts/validation/phase2-prep/`; NVIDIA's official
https://docs.nvidia.com/deploy/cuda-compatibility/ documentation. Driver CUDA
support shown by nvidia-smi is not the same as an installed CUDA toolkit.

## Prepared environment and limits

`configs/phase2-requirements.in` pins vLLM 0.33.0 and this package's build/runtime
requirements. `configs/phase2-linux-py312-cu13.lock` contains **200 resolved,
hashed packages** for Python 3.12 / x86_64-manylinux_2_39. Resolution used wheel
metadata only: nothing from the GPU stack was installed, imported or run here.

The initial x86_64-manylinux_2_28 wheel-only resolution failed because the allowed
llguidance 1.7.x wheels were incompatible with that libc target (the inspected
1.7.6 Linux ABI3 wheel is manylinux_2_31). The 2.39 target then resolved. Both the
failure and successful resolutions are saved, with command/exit metadata, in
`artifacts/validation/phase2-prep/dependency_resolution.json`. This establishes a
candidate dependency graph, not a tested installation, wheel ABI, driver match,
model fit or runtime.

Keep the CPU test environment `.venv` separate from `.venv-gpu`. Do not install
the CPU development lock over the GPU environment or combine incompatible
PyTorch/CUDA wheels. Do not loosen the vLLM pin or force dependencies after a
resolver error. The final source candidate remains
`4ba787ec9959e566d3b587a796dff07673324da5`; a version number alone does not prove
an installed binary was built from that commit.

## First command once access exists

In the **administrator-approved allocated compute shell**, run:

```bash
nvidia-smi --query-gpu=uuid,name,driver_version,memory.total --format=csv
```

This is the first GPU-specific command. It is discovery, not a workload. Retain
its real output and match UUIDs to the allocation before any sampling. Then
follow `PHASE2_EXECUTION_PLAN.md`. Stop if the allocated device is unavailable,
permission is denied, allocation identity is ambiguous, or the candidate stack
is incompatible. No physical workload is authorized or launched by this CPU
preparation task.
