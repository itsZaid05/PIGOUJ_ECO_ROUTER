# First task to paste into Codex

You are the senior systems engineer and research implementer for **PIGOU-J v7**. All context is already in this repository. Read `AGENTS.md`, `README.md`, `docs/ARCHITECTURE_CONTRACTS.md`, `docs/PHASE_PLAN.md`, `docs/VALIDATION_GATES.md`, and the canonical v7 Markdown paper. Consult earlier PDFs only for specific failure modes. Do not revert to the older four-stage online GPU-energy estimator.

**Perform Phase 0 and the CPU-only part of Phase 1 now, in the repository:**

1. Audit the actual workspace: OS/architecture, Python/Codex/Git availability, CUDA/NVIDIA access, GPU identity and energy sensor support *if present*, existing repo files. Do not assume the development host has an NVIDIA GPU.
2. Write `docs/ENVIRONMENT_AUDIT.md` with measured commands/results, hardware limitations, and the chosen phase-1 mode (CPU mock or real Linux/NVIDIA). Check the vLLM V1 API against the exact version installed/available, not a stale hypothetical remote admission API. Do not install vLLM on macOS merely to claim GPU support.
3. Set up a clean Python research package with `pyproject.toml`, lint/test tooling and clear modules: `schemas`, `engine_adapter` (protocol + deterministic mock), `replay`, `energy`, `routing`, `validation`; tests under `tests/`. Do **not** create fabricated GPU experiments or assume native engine hooks work.
4. Implement **only** the strongly typed trace/request/state/action/energy-boundary schemas, immutable run manifests, replay fingerprint comparison, a deterministic *mock* engine adapter with deliberate rejection/staleness behavior, and unit tests for these contracts.
5. Implement a minimal two-arm CPU **harness** that generates correctly labelled *synthetic demonstration* pairs and validates common horizon, identical offered-prefix hashes, intervention/omission semantics, paired seed/order metadata, admission failures, and boundary consistency. This must never be passed off as physical training data.
6. Run the existing reference tests and your new real unit tests, lint and type checks. Save exact outputs under `artifacts/validation/` (or commit test-output evidence) and update the decision log.

**Do not yet:** train an incremental-energy model, patch vLLM internals blindly, execute costly GPU jobs, report physical energy gains, or build a UI. The first goal is verified data contracts and a reproducible harness. Keep abstractions small and executable.

**Final response of this Codex task:** list files added/changed, exact test commands/results, demonstrated guarantees versus assumptions, any missing engine/telemetry capability, and next-phase GO/NO-GO. If something cannot be tested, state it explicitly and leave a reproducible pending test. No generic outline-only answer—write and execute the CPU-only foundation now.
