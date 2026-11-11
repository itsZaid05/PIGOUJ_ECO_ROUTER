"""Independent regressions against the Gate A acceptance contract."""

import pytest
from pydantic import ValidationError

from pigouj.engine_adapter import MockEngineAdapter
from pigouj.harness import demo_request, generate_pair
from pigouj.replay import fingerprint
from pigouj.routing import attempt_once
from pigouj.schemas import CounterSample, EngineStateSnapshot, RunRecord
from pigouj.validation import validate_pair
from tests.conftest import change


def with_state(run: RunRecord, state: EngineStateSnapshot) -> RunRecord:
    return change(
        run,
        initial_state=state,
        manifest=change(run.manifest, initial_fingerprint=fingerprint(state)),
    )


def test_wrong_worker_snapshot_cannot_authorize_another_worker() -> None:
    target = MockEngineAdapter(worker_id="target")
    other = MockEngineAdapter(worker_id="other")
    before = target.observe_state(5)
    with pytest.raises(ValueError, match="worker"):
        attempt_once(target, demo_request(), other.observe_state(5))
    assert target.observe_state(5) == before


def test_future_request_is_rejected_before_mock_state_mutates() -> None:
    engine = MockEngineAdapter()
    before = engine.observe_state(0)
    with pytest.raises(ValueError, match="arrival"):
        attempt_once(engine, demo_request(arrival_ns=5), before)
    assert engine.observe_state(0) == before


@pytest.mark.parametrize("field", ["active", "waiting", "cache_prefix_hashes"])
def test_snapshot_queue_or_cache_membership_must_be_unique(
    pair: tuple[RunRecord, RunRecord],
    field: str,
) -> None:
    state = pair[0].initial_state
    observation = getattr(state, field)
    duplicate: tuple[object, ...]
    if field == "active":
        values = state.active.value
        assert values is not None
        duplicate = (values[0], values[0])
    else:
        duplicate = ("a" * 64, "a" * 64)
    with pytest.raises(ValidationError, match="duplicate"):
        change(state, **{field: change(observation, value=duplicate)})


def test_snapshot_running_and_waiting_ids_cannot_overlap(pair: tuple[RunRecord, RunRecord]) -> None:
    state = pair[0].initial_state
    assert state.active.value is not None
    with pytest.raises(ValidationError, match="overlap"):
        change(state, waiting=change(state.waiting, value=(state.active.value[0].request_id,)))


@pytest.mark.parametrize(
    "field",
    [
        "active",
        "waiting",
        "kv_free_blocks",
        "scheduler_budget",
        "cache_prefix_hashes",
        "cache_epoch",
    ],
)
def test_equal_missing_core_state_does_not_prove_matching_initial_state(
    pair: tuple[RunRecord, RunRecord],
    field: str,
) -> None:
    changed = []
    for run in pair:
        observation = getattr(run.initial_state, field)
        state = change(
            run.initial_state,
            **{
                field: change(observation, value=None, provenance="missing"),
            },
        )
        changed.append(with_state(run, state))
    verdict = validate_pair(changed[0], changed[1])
    assert verdict.status == "invalid" and verdict.delta_j is None
    assert f"baseline:initial_state_missing:{field}" in verdict.reasons


def test_equal_old_mock_observations_are_not_current_state(
    pair: tuple[RunRecord, RunRecord],
) -> None:
    changed = []
    for run in pair:
        state = change(
            run.initial_state,
            kv_free_blocks=change(
                run.initial_state.kv_free_blocks,
                observed_at_ns=0,
            ),
        )
        changed.append(with_state(run, state))
    verdict = validate_pair(changed[0], changed[1])
    assert verdict.status == "invalid" and verdict.delta_j is None
    assert "baseline:initial_state_stale:kv_free_blocks" in verdict.reasons


def test_equal_unknown_active_request_is_not_an_offered_prefix(
    pair: tuple[RunRecord, RunRecord],
) -> None:
    changed = []
    for run in pair:
        active = run.initial_state.active
        assert active.value is not None
        state = change(
            run.initial_state,
            active=change(
                active,
                value=(change(active.value[0], request_id="never-offered"),),
            ),
        )
        changed.append(with_state(run, state))
    verdict = validate_pair(changed[0], changed[1])
    assert verdict.status == "invalid" and verdict.delta_j is None
    assert "baseline:initial_state_unoffered_request" in verdict.reasons


def test_completed_output_cannot_extend_past_recorded_drain(
    pair: tuple[RunRecord, RunRecord],
) -> None:
    baseline, intervention = pair
    outcomes = tuple(
        change(o, ttft_ns=10_000) if o.request_id == "candidate" else o
        for o in intervention.outcomes
    )
    verdict = validate_pair(baseline, change(intervention, outcomes=outcomes))
    assert verdict.status == "invalid" and verdict.delta_j is None
    assert "intervention:completion_outside_recorded_window" in verdict.reasons


@pytest.mark.parametrize("missing", ["flag", "empty", "null", "reset", "unsorted"])
def test_missing_or_invalid_energy_excluded_by_pair_verifier(
    pair: tuple[RunRecord, RunRecord],
    missing: str,
) -> None:
    baseline, intervention = pair
    sample_sets = {
        "empty": (),
        "null": (
            CounterSample(elapsed_ns=0, cumulative_j=100.0),
            CounterSample(elapsed_ns=100, cumulative_j=None),
        ),
        "reset": (
            CounterSample(elapsed_ns=0, cumulative_j=100.0),
            CounterSample(elapsed_ns=100, cumulative_j=99.0),
        ),
        "unsorted": (
            CounterSample(elapsed_ns=0, cumulative_j=100.0),
            CounterSample(elapsed_ns=60, cumulative_j=101.0),
            CounterSample(elapsed_ns=50, cumulative_j=102.0),
            CounterSample(elapsed_ns=100, cumulative_j=103.0),
        ),
    }
    energy = (
        change(intervention.energy, missing_data=True)
        if missing == "flag"
        else change(intervention.energy, samples=sample_sets[missing])
    )
    verdict = validate_pair(baseline, change(intervention, energy=energy))
    assert verdict.status == "invalid" and verdict.delta_j is None
    assert any(reason.startswith("intervention:energy:") for reason in verdict.reasons)


@pytest.mark.parametrize("scenario", ["capacity", "stale_epoch"])
def test_actual_failed_admission_is_not_a_large_energy_label(scenario: str) -> None:
    if scenario == "capacity":
        baseline, intervention, verdict = generate_pair("capacity")
    else:
        baseline, intervention, verdict = generate_pair("stale_epoch")
    assert intervention.admission is not None and not intervention.admission.accepted
    assert intervention.admission.reason == scenario
    assert verdict.status == "infeasible" and verdict.delta_j is None
    outcome = next(o for o in intervention.outcomes if o.request_id == "candidate")
    assert outcome.status == "rejected" and outcome.reason == scenario
    assert outcome.generated_tokens is outcome.ttft_ns is outcome.tpot_ns is None
    assert len(baseline.outcomes) == len(intervention.outcomes) == 3


@pytest.mark.parametrize(("counter_end", "expected"), [(101.0, -4.0), (105.0, 0.0), (109.0, 4.0)])
def test_labels_preserve_negative_zero_and_positive_signs(
    pair: tuple[RunRecord, RunRecord],
    counter_end: float,
    expected: float,
) -> None:
    baseline, intervention = pair
    energy = change(
        intervention.energy,
        samples=(
            CounterSample(elapsed_ns=0, cumulative_j=100.0),
            CounterSample(elapsed_ns=100, cumulative_j=counter_end),
        ),
    )
    verdict = validate_pair(baseline, change(intervention, energy=energy))
    assert verdict.status == "valid" and verdict.delta_j == expected
    assert verdict.evidence == "synthetic_demonstration" and verdict.units == "J"
    assert verdict.eligible_for_physical_training is False


def test_committed_baseline_pair_verdicts_remain_unchanged() -> None:
    import json
    from pathlib import Path

    root = Path(__file__).resolve().parents[1] / "artifacts/validation/synthetic_demo"
    pairs: dict[str, dict[str, RunRecord]] = {}
    for line in (root / "runs.jsonl").read_text().splitlines():
        run = RunRecord.model_validate_json(line)
        pairs.setdefault(run.manifest.pair_id, {})[run.manifest.arm] = run
    original = [json.loads(line) for line in (root / "pair_ledger.jsonl").read_text().splitlines()]
    assert len(original) == 8
    for verdict in original:
        pair = pairs[verdict["pair_id"]]
        actual = validate_pair(pair["baseline"], pair["intervention"])
        assert actual.model_dump(mode="json") == verdict
