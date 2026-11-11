"""Protocol plus a deterministic, single-threaded test double.

The mock's slots, cache membership and virtual completion times are arbitrary
test mechanics. They do not emulate vLLM allocation, GPU timing or native hooks.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from pigouj.schemas import (
    AdmissionResult,
    EngineStateSnapshot,
    Observation,
    RequestOutcome,
    RequestProgress,
    RequestRecord,
    content_hash,
)

MOCK_VERSION = "deterministic-test-double/1"
MOCK_COMMIT = content_hash(MOCK_VERSION)
MODEL_HASH = content_hash("synthetic-model-no-weights")


class EngineAdapter(Protocol):
    @property
    def worker_id(self) -> str: ...

    def observe_state(self, now_ns: int) -> EngineStateSnapshot: ...

    def can_attempt_admission(self, request: RequestRecord) -> bool | None:
        """Advisory only; never a reservation or acceptance."""
        ...

    def attempt_admission(self, request: RequestRecord, expected_epoch: int) -> AdmissionResult: ...

    def measure_engine_overhead(self) -> Observation[float]: ...

    def list_caps(self) -> tuple[str, ...]: ...


@dataclass(frozen=True)
class Pending:
    request: RequestRecord
    slots: int
    first_token_ns: int
    finish_ns: int


class MockEngineAdapter:
    def __init__(self, capacity: int = 32, worker_id: str = "mock-worker-0") -> None:
        if capacity < 0:
            raise ValueError("capacity cannot be negative")
        self.capacity = capacity
        self.worker_id = worker_id
        self.epoch = 0
        self.now_ns = 0
        self._pending: dict[str, Pending] = {}
        self._outcomes: dict[str, RequestOutcome] = {}
        self._seen: set[str] = set()
        self._cache: set[str] = set()
        self._operations = 0

    @property
    def config_hash(self) -> str:
        return content_hash({"capacity": self.capacity, "mechanics": MOCK_VERSION})

    def list_caps(self) -> tuple[str, ...]:
        return ("mock_only", "deterministic", "epoch_rejection", "capacity_rejection")

    def measure_engine_overhead(self) -> Observation[float]:
        return Observation[float](
            value=float(self._operations),
            provenance="estimated",
            observed_at_ns=self.now_ns,
            source="mock operation count; dimensionless, not measured time or energy",
        )

    def _used(self) -> int:
        return sum(p.slots for p in self._pending.values())

    def _slots(self, request: RequestRecord) -> int:
        # Exact tuple/hash equality is only a toy cache predicate.
        prompt = content_hash((request.prompt_tokens, request.prompt_token_hash))
        return request.max_completion_tokens + (
            0 if prompt in self._cache else request.prompt_length
        )

    def can_attempt_admission(self, request: RequestRecord) -> bool | None:
        return self._used() + self._slots(request) <= self.capacity

    def invalidate_snapshot(self) -> None:
        """Deliberately simulate an intervening engine state change."""
        self.epoch += 1

    def attempt_admission(self, request: RequestRecord, expected_epoch: int) -> AdmissionResult:
        if request.arrival_ns > self.now_ns:
            raise ValueError("request arrival is after the mock engine clock")
        self._operations += 1
        before = self.epoch
        reason: str
        if expected_epoch != self.epoch:
            reason = "stale_epoch"
        elif request.request_id in self._seen:
            reason = "duplicate"
        elif request.model_id != "synthetic-model":
            reason = "model_mismatch"
        elif self._used() + self._slots(request) > self.capacity:
            reason = "capacity"
        else:
            reason = "accepted"
        accepted = reason == "accepted"
        if accepted:
            # Virtual ticks deliberately have no relationship to a real scheduler.
            first = self.now_ns + 10 + 5 * len(self._pending)
            finish = first + 10 * (request.max_completion_tokens - 1)
            self._pending[request.request_id] = Pending(
                request, self._slots(request), first, finish
            )
            self._seen.add(request.request_id)
            self.epoch += 1
        # Validation occurs at this narrow dynamic-string boundary as well.
        return AdmissionResult.model_validate(
            {
                "request_id": request.request_id,
                "worker_id": self.worker_id,
                "accepted": accepted,
                "reason": reason,
                "epoch_before": before,
                "epoch_after": self.epoch,
                "source": "mock",
            }
        )

    def advance(self, now_ns: int) -> None:
        if now_ns < self.now_ns:
            raise ValueError("mock clock cannot move backwards")
        for key, pending in tuple(self._pending.items()):
            if pending.finish_ns <= now_ns:
                request = pending.request
                self._outcomes[key] = RequestOutcome(
                    request_id=key,
                    status="completed",
                    reason="synthetic_fixed_length",
                    generated_tokens=request.max_completion_tokens,
                    ttft_ns=pending.first_token_ns - request.arrival_ns,
                    tpot_ns=None if request.max_completion_tokens == 1 else 10,
                )
                self._cache.add(content_hash((request.prompt_tokens, request.prompt_token_hash)))
                del self._pending[key]
                self.epoch += 1
        self.now_ns = now_ns

    def outcomes_at(self, end_ns: int) -> tuple[RequestOutcome, ...]:
        self.advance(end_ns)
        unfinished = tuple(
            RequestOutcome(
                request_id=key,
                status="censored",
                reason="synthetic_horizon_exhausted",
                generated_tokens=None,
                ttft_ns=None,
                tpot_ns=None,
            )
            for key in self._pending
        )
        return tuple(self._outcomes.values()) + unfinished

    @property
    def drain_at_ns(self) -> int:
        return max((p.finish_ns for p in self._pending.values()), default=self.now_ns)

    def observe_state(self, now_ns: int) -> EngineStateSnapshot:
        self.advance(now_ns)
        return EngineStateSnapshot(
            captured_at_ns=now_ns,
            worker_id=self.worker_id,
            engine_version=MOCK_VERSION,
            engine_commit=MOCK_COMMIT,
            model_hash=MODEL_HASH,
            runtime_config_hash=self.config_hash,
            epoch=self.epoch,
            active=Observation[tuple[RequestProgress, ...]](
                value=tuple(
                    RequestProgress(
                        request_id=key,
                        generated_tokens=max(0, (now_ns - p.first_token_ns) // 10 + 1),
                    )
                    for key, p in self._pending.items()
                ),
                provenance="estimated",
                observed_at_ns=now_ns,
                source="mock pending ledger",
            ),
            waiting=Observation[tuple[str, ...]](
                value=(),
                provenance="estimated",
                observed_at_ns=now_ns,
                source="mock no queue",
            ),
            kv_free_blocks=Observation[int](
                value=self.capacity - self._used(),
                provenance="estimated",
                observed_at_ns=now_ns,
                source="mock slots; not physical KV blocks",
            ),
            scheduler_budget=Observation[int](
                value=self.capacity,
                provenance="estimated",
                observed_at_ns=now_ns,
                source="mock slots; not native scheduler budget",
            ),
            cache_prefix_hashes=Observation[tuple[str, ...]](
                value=tuple(sorted(self._cache)),
                provenance="estimated",
                observed_at_ns=now_ns,
                source="mock cache membership; not engine prefix hits",
            ),
            cache_epoch=Observation[int](
                value=len(self._cache),
                provenance="estimated",
                observed_at_ns=now_ns,
                source="mock cache set size",
            ),
            gpu_identity=Observation[str](
                value=None,
                provenance="missing",
                observed_at_ns=now_ns,
                source="no GPU in mock",
            ),
            clock_mhz=Observation[float](
                value=None,
                provenance="missing",
                observed_at_ns=now_ns,
                source="no GPU in mock",
            ),
            temperature_c=Observation[float](
                value=None,
                provenance="missing",
                observed_at_ns=now_ns,
                source="no GPU in mock",
            ),
        )
