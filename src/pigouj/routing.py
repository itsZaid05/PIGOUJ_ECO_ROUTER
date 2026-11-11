"""A single contract-level attempt; no scorer or production router in Phase 1."""

from pigouj.engine_adapter import EngineAdapter
from pigouj.schemas import AdmissionResult, EngineStateSnapshot, RequestRecord


def attempt_once(
    adapter: EngineAdapter,
    request: RequestRecord,
    snapshot: EngineStateSnapshot,
) -> AdmissionResult:
    """Only the adapter can accept. Advisory feasibility never forces success."""
    return adapter.attempt_admission(request, expected_epoch=snapshot.epoch)
