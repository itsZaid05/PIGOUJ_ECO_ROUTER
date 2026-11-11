# Phase 0 environment audit — 11 November 2026

**Chosen Phase 1 mode: CPU mock.** No NVIDIA device or physical energy source is exposed to this execution workspace. This is a Linux container/VM audit, not an inventory of the provider's underlying hardware. GPU identity and NVIDIA energy-counter support cannot be tested here.

Measured at `2026-11-11T14:01:10Z`; raw command arguments, stdout/stderr, exit codes, package metadata and file inventory are in `artifacts/validation/environment_raw.json`. Reproduce with `python3 scripts/audit_environment.py` from the repository root. The inventory was captured immediately after extraction and creation of that audit script, before the implementation package existed.

| Probe | Observed result |
|---|---|
| `uname -a` | Linux `6.18.57`, x86_64; full output in raw evidence |
| `cat /etc/os-release` | Debian GNU/Linux 13 (trixie), Debian version 13.6 |
| `lscpu` | 3 exposed logical CPUs, Intel Xeon Platinum 8573C, KVM guest |
| `python3 --version` | Python 3.12.14 |
| `python3 -m pip --version` | Base environment pip 26.2.2 |
| `codex --version` | codex-cli 0.167.0-alpha.4; exit 0 with read-only PATH-alias warning |
| `git --version` | git version 2.52.0 |
| Initial `git status --short` | Exit 128: archive had no Git repository |
| `nvcc --version` | Executable absent; no CUDA compiler exposed |
| `nvidia-smi -L` and UUID/name/driver/memory query | Executable absent; no GPU identity or driver result available |
| `/dev/nvidia*`, `/proc/driver/nvidia/version` | No device nodes; driver-version path absent |
| `ctypes.util.find_library('nvidia-ml')` | `None`; NVML unavailable in this workspace |
| `/sys/class/powercap/**/energy_uj` | No exposed RAPL energy files |
| Installed package metadata | No vLLM, torch or nvidia-ml-py installed |

The container's absence of a GPU does **not** establish that any particular NVIDIA model lacks energy-counter support. `nvmlDeviceGetTotalEnergyConsumption`, counter resolution, drift, PDU calibration, and CPU/GPU sensor overlap all remain untested. No PDU endpoint, meter credentials, model checkpoint or GPU host was supplied. Managed environment status reported no configured secrets and an enforced unrestricted network policy. No credentials were read or emitted.

## Exact vLLM V1 source capability check

No installed vLLM API could be executed. A PyPI availability query returned **0.33.0**. Its official GitHub tag `v0.33.0` resolved to **`4ba787ec9959e566d3b587a796dff07673324da5`**. This revision is an inspected candidate for Phase 2, not an installed or validated serving configuration. Source retrieval used TLS verification; no vLLM/CUDA packages or model weights were installed.

Reproduce the pinned inspection:

```bash
.venv/bin/python scripts/inspect_vllm_source.py \
  --version 0.33.0 \
  --expected-commit 4ba787ec9959e566d3b587a796dff07673324da5
```

`artifacts/validation/vllm_api_audit.json` records URLs, exact method signatures, source SHA-256 hashes, and `execution_verified: false`. The five inspected source files and upstream license are retained under `artifacts/validation/vllm_source/` as evidence; they are excluded from our lint/type targets and never executed.

Source findings at this exact revision:

- `vllm/v1/core/kv_cache_manager.py:380`: internal `allocate_slots(...) -> KVCacheBlocks | None`, including `full_sequence_must_fit`, `reserved_blocks`, and cache/encoder/lookahead inputs. Capacity paths return `None`.
- `full_sequence_must_fit` uses `min(request.num_tokens, max_model_len)` in this source. It must not be read as a gateway reservation of every possible future output token up to `max_tokens`.
- `vllm/v1/core/sched/scheduler.py:2931`: `add_request(...) -> None` enqueues work; it does not return an atomic admission/reservation result. At lines 1435–1461, scheduling calls `allocate_slots`, and insufficient capacity breaks scheduling for that request. Queued, scheduled, deferred and rejected are different outcomes.
- `vllm/v1/engine/core.py:518` and `vllm/v1/engine/async_llm.py:397,726`: request submission/generation interfaces exist. Submission is not proof of physical KV allocation.
- The five inspected files contain no `try_admit` or `expected_epoch`. This is a bounded source inspection, not an exhaustive theorem about every extension or route. There is no evidence supporting use of the hypothesized remote atomic admission API.

Our protocol's epoch-checked admission is implemented **only by the mock**. A real adapter needs pinned engine-side allocation/scheduling event instrumentation and a documented interpretation of queue/defer/reject, or a separately reviewed native admission patch. No native hook is assumed to work; none was patched.

## Repository and reproducibility

The archive contained 28 files: research/specification documents and eight reference math checks; no package, implementation tests, GPU adapter or raw physical data. Historical PDFs and the canonical v7 research source remain byte-for-byte unchanged. Earlier PDFs were unnecessary for this bounded task; the v7 contracts already identified the relevant failure modes. Later-phase prompt documents were treated as context, not instructions to execute those phases.

A local Git repository was initialized to preserve the supplied baseline at `b7acf7bfb610ffd0f52d1c227acc53d403ffd333`; no remote is configured and nothing is published. Phase 0/CPU Phase 1 is recorded by local tag `phase0-1-cpu`.

Python dependencies live in `.venv/`, isolated from the base interpreter. `pyproject.toml` pins direct dependencies and `requirements-dev.lock` pins the full resolved CPU development toolchain (including pip 25.0.1 in this venv). Tested interpreter: Python 3.12.14. Python 3.11+ is declared but other interpreters and macOS were not tested. No GPU dependencies are required by CPU tests. See README for clean setup and `scripts/validate_cpu.py` for the exact gate commands.

**Decision:** Phase 0/CPU Phase 1 can complete with recorded CPU evidence. Physical Phase 2 execution is NO-GO on this host; see `docs/PENDING_TESTS.md` for the executable capability probe and unimplemented integration checks.
