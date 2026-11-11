# Decisions and verification ledger

| Date | Decision | Evidence / assumption | Current status |
|---|---|---|---|
| 2026-11-11 | v7 is canonical, earlier designs are historical | Independent research synthesis and prior failure audits | Architecture candidate |
| 2026-11-11 | Offline physical paired-replay labels replace production four-stage symbolic GPU model | Engine scheduling and cache semantics too complex for hand-built exact model | Proposed, unimplemented |
| 2026-11-11 | Native engine admission is authoritative | Gateway KV shadow is non-atomic and stale | Contract defined; integration not verified |
| 2026-11-11 | First test uses homogeneous replicas | Removes model-quality confound | Planned |
| 2026-11-11 | Reference math suite has 8 passed checks | `reference/PIGOUJ_test_results.txt` | Verified toy/math only |
| 2026-11-11 | No measured energy result exists yet | No GPU experiment / raw hardware data | Unverified |

**Codex must append new rows after every phase with git commit and test/log references.**
