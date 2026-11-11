# Project context for engineers (research lineage, not product requirements)

## Origin and motivation
The project began as **AER (Adaptive Eco-Routing)**, a carbon/energy-aware LLM inference routing research effort recognized with a Best Paper award in its student-research conference session (TICSR 2026). The subsequent experiments and research exploration led through CORTEX and MORPH-KV to PIGOU-J. Some related prototype work used a short hackathon implementation to demonstrate routing/RL ideas; these were not comprehensive physical validations of the full research architecture.

The user wants a publication-quality, independently defensible systems contribution, not a hackathon demo or a UI-led prototype. High scientific standards matter more than feature count.

## What to preserve
- Multi-worker energy-vs-latency research objective.
- Physical distinction between **attribution** and **incremental admission cost**.
- Importance of batching, prefill/decode, prefix cache and GPU hardware state.
- Explicit baseline fairness, repeatable physical measurement and strong reproducibility.
- A single falsifiable research result suitable for peer review.

## What the history taught us NOT to build first
- Static J/token constants treated as physical truth.
- Hand-crafted four-stage GPU scheduler claimed physically exact.
- Custom gateway KV block counting treated as a substitute for native scheduler allocation.
- Safety/control theorems disconnected from runtime timing and actual labels.
- Concurrently adding carbon arbitrage, online RL, DVFS, semantic caching, and two-tier quality gating.
- Mock tests passed off as measured GPU performance.

## Canonical novelty hypothesis
Given matched serving substrate and workload, a predictor trained on paired **physical** `E_admit - E_omit` examples and conditioned on **pre-admission worker state** yields better worker rankings and end-to-end Joules per goodput token than simpler queue/cache/energy baselines, without worsening latency and rejection performance. This remains untested.

## Do not overfit to prestige
There are no measured claims of 4%, 7%, 56%, sub-0.05 ms or 2% reconciliation in this project's implementation. Treat numbers appearing in prior research papers or old internal documents as outside results or abandoned target assumptions, not verified PIGOU-J performance.
