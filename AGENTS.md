# PIGOU-J — Repository instructions for Codex

## Mission
Build a reproducible research implementation of **PIGOU-J v7**, not v6. The active spec is `research/v7/PIGOUJ_Final_Research_Architecture_2026.md`. The central, falsifiable contribution is *state-conditioned paired counterfactual marginal-energy admission*. Prior versions in `research/history/` are historical only.

## Invariants (non-negotiable)
1. Never invent measured joules, model accuracy, GPU timings, cache hits or experiment outcomes. Mark synthetic, mock, estimated, predicted and measured values with distinct names/metadata.
2. Energy comparisons: same defined physical boundary, common wall-clock horizon and matched initial state; account for whole run idle and all in-boundary gateway/audit overhead. Baseline omits the candidate, intervention admits it to a specified worker.
3. The physical allocator/scheduler is authoritative. Gateway capacity estimates are advisory. Never bypass native admission failure; no claim of an existing remote atomic reservation RPC without checking the pinned engine version.
4. No CUDA process fork/snapshot claim. Reconstruct matched states from repeated deterministic request-history prefixes, log mismatch/failures, randomize experiment-arm order.
5. No post-treatment feature leakage into online predictors; hold out complete traces/sessions, not random rows from the same run.
6. Prevent rejection-based energy games: record offered traffic, completed requests, rejects, TTFT/TPOT, goodput, total measured energy, and router overhead for every policy.
7. Do not introduce Lyapunov proofs, IW-dACI, RL, carbon, DVFS, semantic caching, MoE routing, or heterogeneous tiers into Phase 1–4. These are optional *later* extensions and require separate evidence.
8. Any proof/claim requires stated assumptions. Unit tests do not establish physical correctness; reference math checks do not establish GPU behavior.

## Implementation method
- Work phase-by-phase according to `docs/PHASE_PLAN.md`; finish one acceptance gate before moving to the next. The user's explicit approval is needed before paid GPU experiments, destructive operations, or substantial hardware use.
- Start with discovery and CPU-only tests. Prefer typed Python 3.11+, pytest, Ruff, explicit `pyproject.toml`, dataclasses/Pydantic for schema contracts, Parquet for immutable event records, and pinned dependencies. Keep optional GPU packages isolated from CPU unit testing.
- Preserve experiment seeds, offered trace hashes, scheduler and model commit hashes, GPU identifiers, meter boundary, run configurations and results in machine-readable manifests.
- Write tests for boundaries, one-token output, cache hits/misses, stale worker state, rejected admissions, batch interference, and replay fingerprint mismatch.
- If an API is missing, implement an adapter interface + safe mock and document the engine patch required. Do **not** simulate pretending it is supported.
- Never modify historical research source PDFs. Corrections belong in `docs/DECISION_LOG.md` and versioned implementation records.

## After every implementation phase
1. Run real tests, formatting and static checks; report commands and exact outputs.
2. Update `docs/DECISION_LOG.md` with decisions, assumptions, status and blockers.
3. Provide changed files, evidence, what is verified, what remains unverified, and a GO/NO-GO decision for the **next** phase only.
4. Do not claim milestone completion if its acceptance artifacts are missing.

## Current readiness
Eight reference **toy/mathematical** checks passed earlier (`reference/`). No vLLM engine integration, paired physical-energy measurement, learned router or full pilot has been completed.
