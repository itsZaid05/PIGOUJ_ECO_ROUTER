# Materials provenance and importance

## Canonical
`research/v7/PIGOUJ_Final_Research_Architecture_2026.md` — v7 technical spec; PDF and DOCX are alternate human-readable formats; `pigouj_arch.png` matches the architecture diagram.

## Reference math
`reference/PIGOUJ_math_checks.py`, `reference/PIGOUJ_test_results.txt` — 8 reference tests; checks do not include vLLM, GPU measurement, or learned routing.

## Historical, **not** current implementation instructions
1. `01_Energy_Aware_LLM_Serving_Architecture_57p.pdf`: AER/CORTEX/MORPH-KV lineage and prior broad objectives.
2. `02_Independent_Research_Validation_Audit_35p.pdf`: earlier mathematical and design audit.
3. `03_Independent_Verification_28p.pdf`: intermediate issue tracking.
4. `04_PIGOUJ_Final_Consolidated_v5_30p.pdf`: first closed-issue claims and four-stage model (now replaced).
5. `05_PIGOUJ_v6_PreExperiment_49p.pdf`: v6 math/integration and attempted tests (not canonical).
6. `06_PIGOUJ_v6_CoreCorrection_19p.pdf`: v6 pseudocode and reported unit tests (not v7 code).

**Priority order for Codex:** `AGENTS.md` > `CODEX_FIRST_PROMPT.md` > `docs/` contracts/gates > v7 Markdown > relevant official engine code > targeted historical materials. Do not transplant v6 code into v7 without explicit critical review.
