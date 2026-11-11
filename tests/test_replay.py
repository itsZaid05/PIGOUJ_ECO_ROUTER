from pathlib import Path

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from pigouj.harness import Scenario, generate_pair, write_demo
from pigouj.replay import fingerprint, fingerprint_differences, randomized_arm_order
from pigouj.schemas import CounterSample, RunRecord
from pigouj.validation import validate_pair
from tests.conftest import change


@pytest.mark.parametrize(
    ("scenario", "status"),
    [
        ("accepted", "valid"),
        ("capacity", "infeasible"),
        ("stale_epoch", "infeasible"),
        ("censored", "censored"),
    ],
)
def test_harness_scenarios(scenario: Scenario, status: str) -> None:
    baseline, intervention, verdict = generate_pair(scenario)
    assert verdict.status == status, verdict.reasons
    assert verdict.evidence == "synthetic_demonstration"
    assert not verdict.eligible_for_physical_training
    assert (verdict.delta_j is not None) == (status == "valid")
    assert baseline.manifest.offered_prefix_hash == intervention.manifest.offered_prefix_hash
    assert baseline.manifest.horizon_ns == intervention.manifest.horizon_ns
    assert len(baseline.outcomes) == len(intervention.outcomes) == 3
    candidate = baseline.candidate.request_id
    assert next(o for o in baseline.outcomes if o.request_id == candidate).status == "omitted"


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("offered_prefix_hash", "a" * 64),
        ("model_hash", "a" * 64),
        ("engine_commit", "b" * 40),
        ("engine_version", "unverified-version"),
        ("runtime_config_hash", "a" * 64),
        ("implementation_hash", "a" * 64),
        ("candidate_hash", "a" * 64),
        ("initial_fingerprint", "a" * 64),
        ("workload_seed", 999),
        ("order_seed", 999),
        ("repeat_id", 99),
        ("horizon_ns", 101),
        ("intervention_at_ns", 6),
        ("cache_policy", "cold"),
        ("meter_id", "different-device"),
    ],
)
def test_mismatched_manifest_never_produces_label(
    pair: tuple[RunRecord, RunRecord],
    field: str,
    value: object,
) -> None:
    baseline, intervention = pair
    bad = change(intervention, manifest=change(intervention.manifest, **{field: value}))
    verdict = validate_pair(baseline, bad)
    assert verdict.status == "invalid" and verdict.delta_j is None
    assert f"pair_mismatch:{field}" in verdict.reasons


def test_boundary_and_timestamp_mismatches_are_rejected(pair: tuple[RunRecord, RunRecord]) -> None:
    baseline, intervention = pair
    changed_boundary = change(
        intervention.energy.boundary, device_ids=("different-virtual-worker",)
    )
    for energy in (
        change(intervention.energy, boundary=changed_boundary),
        change(intervention.energy, start_ns=1),
        change(intervention.energy, end_ns=101),
        change(intervention.energy, missing_data=True),
    ):
        verdict = validate_pair(baseline, change(intervention, energy=energy))
        assert verdict.status == "invalid" and verdict.delta_j is None


def test_manifest_hash_cannot_hide_altered_offered_prefix(
    pair: tuple[RunRecord, RunRecord],
) -> None:
    baseline, intervention = pair
    request = change(intervention.offered_prefix.requests[0], arrival_ns=1)
    prefix = change(
        intervention.offered_prefix, requests=(request, intervention.offered_prefix.requests[1])
    )
    verdict = validate_pair(baseline, change(intervention, offered_prefix=prefix))
    assert "intervention:offered_prefix_content_hash" in verdict.reasons
    assert verdict.delta_j is None


def test_fingerprint_comparison_catches_cache_and_batch_state(
    pair: tuple[RunRecord, RunRecord],
) -> None:
    baseline, intervention = pair
    state = intervention.initial_state
    cache = change(state.cache_prefix_hashes, value=("a" * 64,))
    changed = change(state, cache_prefix_hashes=cache)
    assert fingerprint(state) != fingerprint(changed)
    assert fingerprint_differences(state, changed) == ("cache_prefix_hashes",)
    bad = change(
        intervention,
        initial_state=changed,
        manifest=change(intervention.manifest, initial_fingerprint=fingerprint(changed)),
    )
    verdict = validate_pair(baseline, bad)
    assert "fingerprint_mismatch:cache_prefix_hashes" in verdict.reasons
    assert verdict.delta_j is None


def test_common_timestamp_shift_in_both_arms_is_still_rejected(
    pair: tuple[RunRecord, RunRecord],
) -> None:
    baseline, intervention = pair
    shifted = tuple(
        change(run, manifest=change(run.manifest, intervention_at_ns=6)) for run in pair
    )
    verdict = validate_pair(shifted[0], shifted[1])
    assert verdict.status == "invalid"
    assert "baseline:snapshot_intervention_timestamp" in verdict.reasons
    assert validate_pair(baseline, intervention).status == "valid"


def test_rejections_cannot_be_relabelled_as_completions(pair: tuple[RunRecord, RunRecord]) -> None:
    baseline, intervention = pair
    missing_admission = change(intervention, admission=None)
    assert validate_pair(baseline, missing_admission).delta_j is None
    outcome = next(o for o in intervention.outcomes if o.request_id == "candidate")
    omitted = change(
        outcome, status="omitted", reason="bad", generated_tokens=None, ttft_ns=None, tpot_ns=None
    )
    outcomes = tuple(omitted if o.request_id == "candidate" else o for o in intervention.outcomes)
    verdict = validate_pair(baseline, change(intervention, outcomes=outcomes))
    assert "intervention:accepted_admission_outcome" in verdict.reasons


def test_offered_ledger_must_include_rejected_and_omitted_requests(
    pair: tuple[RunRecord, RunRecord],
) -> None:
    baseline, intervention = pair
    for outcomes in (intervention.outcomes[:-1], intervention.outcomes + intervention.outcomes[:1]):
        verdict = validate_pair(baseline, change(intervention, outcomes=outcomes))
        assert "intervention:offered_request_outcome_ledger" in verdict.reasons
        assert verdict.delta_j is None


def test_negative_difference_is_legal_and_has_canonical_sign(
    pair: tuple[RunRecord, RunRecord],
) -> None:
    baseline, intervention = pair
    # Assigned fixture counters deliberately cover a negative signed difference.
    energy = change(
        intervention.energy,
        samples=(
            CounterSample(elapsed_ns=0, cumulative_j=100.0),
            CounterSample(elapsed_ns=100, cumulative_j=101.0),
        ),
    )
    verdict = validate_pair(baseline, change(intervention, energy=energy))
    assert verdict.status == "valid" and verdict.delta_j == -4.0


@settings(max_examples=30, derandomize=True)
@given(
    order_seed=st.integers(0, 10_000),
    workload_seed=st.integers(0, 10_000),
    repeat=st.integers(0, 100),
)
def test_paired_seed_order_and_content_are_reproducible(
    order_seed: int,
    workload_seed: int,
    repeat: int,
) -> None:
    a, b, verdict = generate_pair("accepted", workload_seed, order_seed, repeat)
    again = generate_pair("accepted", workload_seed, order_seed, repeat)
    assert (a, b, verdict) == again
    assert a.manifest.arm_order == randomized_arm_order(order_seed, repeat)
    assert a.manifest.workload_seed == b.manifest.workload_seed == workload_seed
    assert a.manifest.execution_index != b.manifest.execution_index
    assert verdict.status == "valid"


def test_arm_order_varies_across_registered_repeats() -> None:
    assert len({randomized_arm_order(17, repeat) for repeat in range(20)}) == 2


def test_physical_pair_validation_is_explicitly_unavailable(
    pair: tuple[RunRecord, RunRecord],
) -> None:
    physical_runs = []
    for run in pair:
        boundary = change(run.energy.boundary, kind="NVML_GPU_BOARDS")
        energy = change(
            run.energy,
            boundary=boundary,
            status="measured",
            evidence="measured",
            wall_origin_unix_ns=1000,
        )
        manifest = change(run.manifest, boundary=boundary, evidence="measured")
        physical_runs.append(change(run, energy=energy, manifest=manifest))
    verdict = validate_pair(physical_runs[0], physical_runs[1])
    assert verdict.status == "invalid" and verdict.delta_j is None
    assert "baseline:physical_engine_adapter_unavailable_in_phase1" in verdict.reasons


def test_candidate_and_prefix_identity_cannot_overlap(pair: tuple[RunRecord, RunRecord]) -> None:
    baseline, intervention = pair
    candidate = change(intervention.candidate, request_id="incumbent-1")
    bad = change(
        intervention,
        candidate=candidate,
        manifest=change(intervention.manifest, candidate_hash=candidate.digest()),
    )
    verdict = validate_pair(baseline, bad)
    assert verdict.status == "invalid" and verdict.delta_j is None
    assert "intervention:candidate_already_in_prefix" in verdict.reasons


def test_censoring_cannot_be_hidden_with_a_drained_flag() -> None:
    baseline, intervention, _ = generate_pair("censored")
    verdict = validate_pair(baseline, change(intervention, drained=True))
    assert verdict.status == "invalid" and verdict.delta_j is None
    assert "intervention:drain_status_inconsistent" in verdict.reasons


def test_missing_state_freshness_cannot_be_moved_to_the_future(
    pair: tuple[RunRecord, RunRecord],
) -> None:
    from pydantic import ValidationError

    state = pair[0].initial_state
    observation = change(state.kv_free_blocks, observed_at_ns=state.captured_at_ns + 1)
    with pytest.raises(ValidationError, match="future"):
        change(state, kv_free_blocks=observation)


def test_output_is_explicit_exclusive_and_roundtrips(fresh_output: Path) -> None:
    summary = write_demo(fresh_output)
    assert summary["physical_measurements"] == 0
    assert summary["statuses"] == {"valid": 2, "invalid": 0, "infeasible": 4, "censored": 2}
    records = [
        RunRecord.model_validate_json(line)
        for line in (fresh_output / "runs.jsonl").read_text().splitlines()
    ]
    assert len(records) == 16
    for a, b in zip(records[::2], records[1::2], strict=True):
        assert (a.manifest.execution_index, b.manifest.execution_index) == (0, 1)
    with pytest.raises(FileExistsError):
        write_demo(fresh_output)
