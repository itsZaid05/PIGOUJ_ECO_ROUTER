# PIGOU-J v7 — Codex research engineering handoff

**Canonical research design:** `research/v7/PIGOUJ_Final_Research_Architecture_2026.md`.
**Current status:** research architecture and conditional mathematics only. No working vLLM adapter, physical paired-counterfactual dataset, trained delta predictor, or measured energy saving exists in this handoff.

## Open this first

1. Read `AGENTS.md` (Codex should load it automatically from the repository root).
2. Read `CODEX_FIRST_PROMPT.md` and paste it as the first task in Codex.
3. Read `docs/ARCHITECTURE_CONTRACTS.md`, `docs/PHASE_PLAN.md`, and `docs/VALIDATION_GATES.md`.
4. Read the canonical v7 Markdown report. Use `research/history/` **only** to understand earlier hypotheses and failure modes; it is not the active implementation spec.
5. Run reference checks: `python3 reference/PIGOUJ_math_checks.py -v`. These are toy-model checks and **not** GPU integration tests.

## Research question

Can a *state-conditioned learned estimate of incremental physical energy from admitting a request to a worker* improve decisions versus fixed token cost, queue-aware placement, and prefix-affinity policies under the same offered workload, model, engine, GPU configuration, SLO, and measurement boundary?

## Core architecture

- Offline: reproducible history-prefix reconstruction -> matched baseline vs intervention arm -> physical energy measurement on common horizon -> paired delta labels -> held-out evaluation -> trained incremental-energy predictor and uncertainty model.
- Online: request descriptor -> engine-observed worker snapshots -> eligibility and tentative feasibility -> predicted incremental energy / latency-risk -> robust selection -> **native engine admission** -> log all outcomes and energy overhead.
- First target is **homogeneous replicas of one model**. Defer cross-model safety gating, RL, carbon, DVFS, semantic cache, and disaggregated serving.

## Repo engineering rules

- Develop the CPU-only foundation and tests on any machine. Do not fabricate CUDA/NVML readings on macOS.
- GPU integration must be on a real supported Linux/NVIDIA testbed or explicitly marked unavailable.
- Do not assume a remotely callable atomic reservation API exists in vLLM; verify the pinned engine's native admission behavior first.
- All results must be backed by raw logs, test results, version/environment records and reproducible commands.
- Do not claim any physical gain until measured.

## What this archive contains

- `research/v7`: current PDF, DOCX, Markdown, and architecture diagram.
- `research/history`: six predecessor/earlier audit PDFs (context only).
- `reference`: independently executed reference math tests and their output (not implementation tests).
- `AGENTS.md`: durable coding-agent instructions.
- `CODEX_FIRST_PROMPT.md`: initial actionable Codex task.
- `docs/`: architecture contracts, phases, experiment protocol, source links, environment setup, risk register, and validation gates.

No API keys, GPU credentials, raw production trace, verified engine patch, or physical measurements are included.

## Executable Phase 0 / CPU Phase 1 foundation

The repository now contains strict frozen v7 contracts, exact replay fingerprint comparison, a deterministic mock engine, and a two-arm **synthetic demonstration** harness. These counters and virtual completion ticks are arbitrary test fixtures. They are neither physical training labels nor a CPU implementation of vLLM's scheduler. There is no learned predictor, GPU adapter or UI.

Clean CPU setup (Python 3.11+, tested on 3.12.14):

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-dev.lock
.venv/bin/python -m pip install --no-build-isolation --no-deps -e .
.venv/bin/python scripts/validate_cpu.py --output work/validation-recheck
```

The recorded acceptance run retains raw outputs and exit codes under `artifacts/validation/`. The command above reruns the gate into a new `work/validation-recheck` directory; select another output path on subsequent runs. The runner refuses to overwrite an existing demonstration directory. Individual test/lint/type commands in `artifacts/validation/commands.json` can also be rerun independently.

For a new demonstration:

```bash
.venv/bin/python -m pigouj.harness --output work/demo-new --repeats 2
```

An output directory must not already exist. Every JSONL record/manifest has an evidence tag; pair records are always `eligible_for_physical_training: false`. The CLI produces accepted, capacity-rejected, stale-epoch and censored cases. Invalid records are tested through deliberate corruptions of real module outputs. Every offered prefix request plus the candidate has a completion/rejection/censoring/omission outcome; counterfactual omission is distinct from deployed rejection. One-token TPOT is undefined, represented by `null`.

Modules are `schemas`, `engine_adapter`, `replay`, `energy`, `routing`, `validation`, and the CLI `harness`. `routing.attempt_once` delegates a single attempt; it is not an online routing policy. JSONL plus exclusive file creation and committed content hashes serve the small immutable CPU evidence set; physical Parquet ingestion is deferred to the physical replay phase.

See `docs/ENVIRONMENT_AUDIT.md`, `docs/CPU_FOUNDATION_REPORT.md` and `docs/PENDING_TESTS.md`. **CPU Gate A can pass while physical Gate B remains blocked.**
