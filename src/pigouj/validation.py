"""Fail-closed pair verification, returning a ledger entry for every attempt."""

from typing import Literal

from pigouj.energy import InvalidEnergy, counter_energy_j
from pigouj.replay import fingerprint, fingerprint_differences, randomized_arm_order
from pigouj.schemas import PairValidation, RunRecord

MATCHED_MANIFEST_FIELDS = (
    "pair_id",
    "repeat_id",
    "arm_order",
    "workload_seed",
    "order_seed",
    "offered_prefix_hash",
    "candidate_hash",
    "initial_fingerprint",
    "intervention_at_ns",
    "horizon_ns",
    "cache_policy",
    "estimand",
    "engine_version",
    "engine_commit",
    "model_hash",
    "runtime_config_hash",
    "implementation_hash",
    "boundary",
    "meter_id",
    "evidence",
)


def _run_errors(run: RunRecord) -> list[str]:
    errors: list[str] = []
    m, state, energy = run.manifest, run.initial_state, run.energy
    if m.evidence != "synthetic_demonstration":
        errors.append("physical_engine_adapter_unavailable_in_phase1")
    if m.offered_prefix_hash != run.offered_prefix.digest():
        errors.append("offered_prefix_content_hash")
    if m.candidate_hash != run.candidate.digest():
        errors.append("candidate_content_hash")
    if m.initial_fingerprint != fingerprint(state):
        errors.append("initial_fingerprint_content_hash")
    if state.captured_at_ns != m.intervention_at_ns:
        errors.append("snapshot_intervention_timestamp")
    if any(r.arrival_ns >= m.intervention_at_ns for r in run.offered_prefix.requests):
        errors.append("future_arrival_in_prefix")
    if run.candidate.arrival_ns != m.intervention_at_ns:
        errors.append("candidate_intervention_timestamp")
    if run.candidate.trace_id != run.offered_prefix.trace_id:
        errors.append("candidate_trace_id")
    if m.evidence == "synthetic_demonstration" and (
        run.candidate.provenance != "synthetic" or run.offered_prefix.provenance != "synthetic"
    ):
        errors.append("input_provenance")
    if m.action.candidate_request_id != run.candidate.request_id:
        errors.append("action_candidate_identity")
    for key in ("engine_version", "engine_commit", "model_hash", "runtime_config_hash"):
        if getattr(m, key) != getattr(state, key):
            errors.append(f"snapshot_{key}")
    if m.arm_order != randomized_arm_order(m.order_seed, m.repeat_id):
        errors.append("arm_order_seed")
    if energy.boundary != m.boundary or energy.meter_id != m.meter_id:
        errors.append("energy_boundary_or_meter_identity")
    if energy.evidence != m.evidence:
        errors.append("energy_evidence")
    if energy.start_ns != 0 or energy.end_ns != m.horizon_ns:
        errors.append("energy_horizon_or_start_timestamp")
    if run.drained != (run.drain_elapsed_ns <= m.horizon_ns):
        errors.append("drain_status_inconsistent")
    try:
        counter_energy_j(energy)
    except InvalidEnergy as exc:
        errors.append(f"energy:{exc}")

    expected_ids = [r.request_id for r in run.offered_prefix.requests]
    if run.candidate.request_id in expected_ids:
        errors.append("candidate_already_in_prefix")
    expected_ids.append(run.candidate.request_id)
    actual_ids = [outcome.request_id for outcome in run.outcomes]
    if sorted(actual_ids) != sorted(expected_ids):
        errors.append("offered_request_outcome_ledger")
    by_id = {outcome.request_id: outcome for outcome in run.outcomes}
    requests = (*run.offered_prefix.requests, run.candidate)
    for request in requests:
        outcome = by_id.get(request.request_id)
        if outcome is None:
            continue
        if outcome.generated_tokens is not None:
            if outcome.generated_tokens > request.max_completion_tokens:
                errors.append("completion_exceeds_hard_cap")
        if outcome.status == "omitted" and request.request_id != run.candidate.request_id:
            errors.append("prefix_request_omitted")
        if run.drained and outcome.status == "censored":
            errors.append("censored_outcome_in_drained_run")

    candidate_outcome = by_id.get(run.candidate.request_id)
    if m.arm == "baseline":
        if run.admission is not None or candidate_outcome is None:
            errors.append("baseline_omission_semantics")
        elif candidate_outcome.status != "omitted":
            errors.append("baseline_omission_semantics")
    else:
        admission = run.admission
        if admission is None or candidate_outcome is None:
            errors.append("intervention_admission_missing")
        else:
            if (
                admission.request_id != run.candidate.request_id
                or admission.worker_id != m.action.worker_id
                or admission.worker_id != state.worker_id
            ):
                errors.append("intervention_admission_identity")
            if admission.accepted:
                if admission.epoch_before != state.epoch:
                    errors.append("accepted_stale_epoch")
                if candidate_outcome.status not in ("completed", "censored"):
                    errors.append("accepted_admission_outcome")
            elif (
                candidate_outcome.status != "rejected"
                or candidate_outcome.reason != admission.reason
            ):
                errors.append("rejected_admission_outcome")
    return errors


def validate_pair(baseline: RunRecord, intervention: RunRecord) -> PairValidation:
    reasons: list[str] = []
    for name in MATCHED_MANIFEST_FIELDS:
        if getattr(baseline.manifest, name) != getattr(intervention.manifest, name):
            reasons.append(f"pair_mismatch:{name}")
    if baseline.manifest.arm != "baseline" or intervention.manifest.arm != "intervention":
        reasons.append("arm_roles")
    if baseline.manifest.run_id == intervention.manifest.run_id:
        reasons.append("duplicate_run_id")
    if baseline.offered_prefix != intervention.offered_prefix:
        reasons.append("offered_prefix_content")
    if baseline.candidate != intervention.candidate:
        reasons.append("candidate_content")
    for field in fingerprint_differences(baseline.initial_state, intervention.initial_state):
        reasons.append(f"fingerprint_mismatch:{field}")
    for arm, run in (("baseline", baseline), ("intervention", intervention)):
        reasons.extend(f"{arm}:{reason}" for reason in _run_errors(run))

    def verdict(
        status: Literal["valid", "invalid", "infeasible", "censored"],
        problems: tuple[str, ...],
        delta_j: float | None = None,
    ) -> PairValidation:
        return PairValidation(
            pair_id=baseline.manifest.pair_id,
            baseline_run_id=baseline.manifest.run_id,
            intervention_run_id=intervention.manifest.run_id,
            evidence=baseline.manifest.evidence,
            status=status,
            reasons=problems,
            delta_j=delta_j,
        )

    if reasons:
        return verdict("invalid", tuple(reasons))
    if intervention.admission is not None and not intervention.admission.accepted:
        return verdict("infeasible", (intervention.admission.reason,))
    if not baseline.drained or not intervention.drained:
        return verdict("censored", ("not_drained",))
    delta = counter_energy_j(intervention.energy) - counter_energy_j(baseline.energy)
    return verdict("valid", (), delta)
