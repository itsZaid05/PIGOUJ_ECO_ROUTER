"""Small, frozen, strictly validated contracts. All times are integer nanoseconds.

Replay times use a run-relative clock; wall origins are recorded separately so
independent executions never pretend to share the same absolute start time.
"""

from __future__ import annotations

import hashlib
import json
from typing import Annotated, Generic, Literal, Self, TypeVar

from pydantic import BaseModel, ConfigDict, Field, model_validator

NonEmpty = Annotated[str, Field(min_length=1)]
Digest = Annotated[str, Field(pattern=r"^[a-f0-9]{64}$")]
SourceRevision = Annotated[str, Field(pattern=r"^(?:[a-f0-9]{40}|[a-f0-9]{64})$")]
Natural = Annotated[int, Field(ge=0)]
Positive = Annotated[int, Field(gt=0)]
NonnegativeFloat = Annotated[float, Field(ge=0, allow_inf_nan=False)]
FiniteFloat = Annotated[float, Field(allow_inf_nan=False)]
Evidence = Literal["synthetic_demonstration", "measured"]
Arm = Literal["baseline", "intervention"]
T = TypeVar("T")


class Frozen(BaseModel):
    model_config = ConfigDict(frozen=True, strict=True, extra="forbid", validate_default=True)

    def digest(self) -> str:
        return content_hash(self.model_dump(mode="json"))


def content_hash(value: object) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)
    return hashlib.sha256(encoded.encode()).hexdigest()


class SamplingSettings(Frozen):
    temperature: NonnegativeFloat
    top_p: Annotated[float, Field(gt=0, le=1, allow_inf_nan=False)]
    seed: Natural


class RequestRecord(Frozen):
    request_id: NonEmpty
    trace_id: NonEmpty
    session_id: NonEmpty
    arrival_ns: Natural
    prompt_length: Natural
    prompt_tokens: tuple[Natural, ...] | None = None
    prompt_token_hash: Digest | None = None
    max_completion_tokens: Positive
    sampling: SamplingSettings
    model_id: NonEmpty
    slo_class: NonEmpty
    provenance: Literal["synthetic", "recorded_with_permission"]

    @model_validator(mode="after")
    def check_tokens(self) -> Self:
        if (self.prompt_tokens is None) == (self.prompt_token_hash is None):
            raise ValueError("provide exactly one of tokens or legally shareable token hash")
        if self.prompt_tokens is not None and len(self.prompt_tokens) != self.prompt_length:
            raise ValueError("prompt length differs from token count")
        return self


class TraceRecord(Frozen):
    trace_id: NonEmpty
    requests: tuple[RequestRecord, ...]
    provenance: Literal["synthetic", "recorded_with_permission"]

    @model_validator(mode="after")
    def check_trace(self) -> Self:
        ids = tuple(r.request_id for r in self.requests)
        arrivals = tuple(r.arrival_ns for r in self.requests)
        if len(ids) != len(set(ids)):
            raise ValueError("duplicate offered request IDs")
        if arrivals != tuple(sorted(arrivals)):
            raise ValueError("offered arrivals must be ordered")
        if any(
            r.trace_id != self.trace_id or r.provenance != self.provenance for r in self.requests
        ):
            raise ValueError("trace identity/provenance mismatch")
        return self


class Observation(Frozen, Generic[T]):
    value: T | None
    provenance: Literal["observed", "estimated", "missing"]
    observed_at_ns: Natural
    source: NonEmpty

    @model_validator(mode="after")
    def check_missing(self) -> Self:
        if (self.provenance == "missing") != (self.value is None):
            raise ValueError("missing observations must be explicit; never substitute zero")
        return self

    def age_ns(self, now_ns: int) -> int:
        if now_ns < self.observed_at_ns:
            raise ValueError("observation is from the future")
        return now_ns - self.observed_at_ns


class RequestProgress(Frozen):
    request_id: NonEmpty
    generated_tokens: Natural


class EngineStateSnapshot(Frozen):
    captured_at_ns: Natural
    worker_id: NonEmpty
    engine_version: NonEmpty
    engine_commit: SourceRevision
    model_hash: Digest
    runtime_config_hash: Digest
    epoch: Natural
    active: Observation[tuple[RequestProgress, ...]]
    waiting: Observation[tuple[NonEmpty, ...]]
    kv_free_blocks: Observation[Natural]
    scheduler_budget: Observation[Natural]
    cache_prefix_hashes: Observation[tuple[Digest, ...]]
    cache_epoch: Observation[Natural]
    gpu_identity: Observation[NonEmpty]
    clock_mhz: Observation[FiniteFloat]
    temperature_c: Observation[FiniteFloat]

    @model_validator(mode="after")
    def check_freshness(self) -> Self:
        for name in type(self).model_fields:
            value = getattr(self, name)
            if isinstance(value, Observation):
                value.age_ns(self.captured_at_ns)
        return self


class Action(Frozen):
    kind: Literal["omit", "admit"]
    candidate_request_id: NonEmpty
    worker_id: NonEmpty | None

    @model_validator(mode="after")
    def check_target(self) -> Self:
        if (self.kind == "omit") != (self.worker_id is None):
            raise ValueError("omit has no worker; admit requires a worker")
        return self


class EnergyBoundary(Frozen):
    boundary_id: NonEmpty
    kind: Literal["SYNTHETIC_CPU_DEMO", "PDU_AC_CLUSTER", "NVML_GPU_BOARDS", "NVML_RAPL_SUBSYSTEM"]
    device_ids: tuple[NonEmpty, ...]
    includes_gateway: bool
    includes_audit: bool
    nonoverlap_verified: bool
    scope_note: NonEmpty

    @model_validator(mode="after")
    def check_devices(self) -> Self:
        if not self.device_ids or len(set(self.device_ids)) != len(self.device_ids):
            raise ValueError("boundary devices must be nonempty and unique")
        if self.kind == "NVML_RAPL_SUBSYSTEM" and not self.nonoverlap_verified:
            raise ValueError("combined subsystem requires verified non-overlapping domains")
        return self


class CounterSample(Frozen):
    elapsed_ns: Natural
    cumulative_j: NonnegativeFloat | None


class EnergyMeasurement(Frozen):
    boundary: EnergyBoundary
    meter_id: NonEmpty
    units: Literal["J"] = "J"
    status: Literal["simulated", "measured"]
    evidence: Evidence
    source: NonEmpty
    start_ns: Natural
    end_ns: Positive
    wall_origin_unix_ns: Natural | None
    samples: tuple[CounterSample, ...]
    missing_data: bool
    uncertainty_j: NonnegativeFloat

    @model_validator(mode="after")
    def check_source(self) -> Self:
        if self.end_ns <= self.start_ns:
            raise ValueError("energy window must have positive duration")
        synthetic = self.evidence == "synthetic_demonstration"
        if synthetic != (self.status == "simulated"):
            raise ValueError("evidence/status mismatch")
        if synthetic != (self.boundary.kind == "SYNTHETIC_CPU_DEMO"):
            raise ValueError("synthetic and physical boundaries cannot be relabelled")
        if not synthetic and self.wall_origin_unix_ns is None:
            raise ValueError("physical readings require a wall-clock origin")
        return self


class RunManifest(Frozen):
    schema_version: Literal["pigouj.v7.cpu-contracts.1"] = "pigouj.v7.cpu-contracts.1"
    run_id: NonEmpty
    pair_id: NonEmpty
    repeat_id: Natural
    arm: Arm
    arm_order: tuple[Arm, Arm]
    execution_index: Annotated[int, Field(ge=0, le=1)]
    workload_seed: Natural
    order_seed: Natural
    offered_prefix_hash: Digest
    candidate_hash: Digest
    initial_fingerprint: Digest
    action: Action
    intervention_at_ns: Natural
    horizon_ns: Positive
    cache_policy: Literal["cold", "warm_prefix_replay"]
    estimand: Literal["isolated_busy_period_no_future_arrivals"]
    engine_version: NonEmpty
    engine_commit: SourceRevision
    model_hash: Digest
    runtime_config_hash: Digest
    implementation_hash: Digest
    boundary: EnergyBoundary
    meter_id: NonEmpty
    evidence: Evidence

    @model_validator(mode="after")
    def check_arm(self) -> Self:
        if set(self.arm_order) != {"baseline", "intervention"}:
            raise ValueError("arm order must be a permutation")
        if self.arm_order[self.execution_index] != self.arm:
            raise ValueError("execution index disagrees with arm order")
        if (self.arm == "baseline") != (self.action.kind == "omit"):
            raise ValueError("baseline omits; intervention attempts admission")
        if (self.evidence == "synthetic_demonstration") != (
            self.boundary.kind == "SYNTHETIC_CPU_DEMO"
        ):
            raise ValueError("manifest evidence/boundary mismatch")
        return self


class AdmissionResult(Frozen):
    request_id: NonEmpty
    worker_id: NonEmpty
    accepted: bool
    reason: Literal["accepted", "capacity", "stale_epoch", "duplicate", "model_mismatch"]
    epoch_before: Natural
    epoch_after: Natural
    source: Literal["mock"]

    @model_validator(mode="after")
    def check_acceptance(self) -> Self:
        if self.accepted != (self.reason == "accepted"):
            raise ValueError("admission reason contradicts outcome")
        expected = self.epoch_before + int(self.accepted)
        if self.epoch_after != expected:
            raise ValueError("rejection cannot mutate epoch; acceptance increments it")
        return self


class RequestOutcome(Frozen):
    request_id: NonEmpty
    status: Literal["completed", "rejected", "omitted", "censored"]
    reason: NonEmpty
    generated_tokens: Natural | None
    ttft_ns: Natural | None
    tpot_ns: Natural | None

    @model_validator(mode="after")
    def check_timing(self) -> Self:
        if self.status == "completed":
            if self.generated_tokens is None or self.generated_tokens < 1 or self.ttft_ns is None:
                raise ValueError("completed request requires positive tokens and TTFT")
            if (self.generated_tokens == 1) != (self.tpot_ns is None):
                raise ValueError("TPOT undefined for one token; required for multiple tokens")
        elif any(x is not None for x in (self.generated_tokens, self.ttft_ns, self.tpot_ns)):
            raise ValueError("non-completions have missing service measurements, not zeros")
        return self


class RunRecord(Frozen):
    manifest: RunManifest
    offered_prefix: TraceRecord
    candidate: RequestRecord
    initial_state: EngineStateSnapshot
    admission: AdmissionResult | None
    outcomes: tuple[RequestOutcome, ...]
    drained: bool
    drain_elapsed_ns: Natural
    energy: EnergyMeasurement


class PairValidation(Frozen):
    pair_id: NonEmpty
    baseline_run_id: NonEmpty
    intervention_run_id: NonEmpty
    status: Literal["valid", "invalid", "infeasible", "censored"]
    reasons: tuple[NonEmpty, ...]
    delta_j: FiniteFloat | None
    evidence: Evidence
    units: Literal["J"] = "J"
    eligible_for_physical_training: Literal[False] = False

    @model_validator(mode="after")
    def check_label(self) -> Self:
        if (self.status == "valid") != (self.delta_j is not None):
            raise ValueError("only a valid pair has an energy difference")
        if (self.status == "valid") != (not self.reasons):
            raise ValueError("invalid/infeasible/censored pairs require reasons")
        return self
