import pytest
from pydantic import ValidationError

from pigouj.harness import demo_request
from pigouj.schemas import (
    Action,
    Observation,
    RequestOutcome,
    RequestRecord,
    RunRecord,
    TraceRecord,
    content_hash,
)
from tests.conftest import change


def test_frozen_nested_manifest_and_serialization(pair: tuple[RunRecord, RunRecord]) -> None:
    baseline, _ = pair
    with pytest.raises(ValidationError, match="frozen"):
        baseline.manifest.horizon_ns = 999  # type: ignore[misc]
    with pytest.raises(ValidationError, match="frozen"):
        baseline.offered_prefix.requests[0].sampling.seed = 8  # type: ignore[misc]
    assert isinstance(baseline.outcomes, tuple)
    restored = RunRecord.model_validate_json(baseline.model_dump_json())
    assert restored == baseline
    assert restored.manifest.digest() == baseline.manifest.digest()


@pytest.mark.parametrize(
    "updates",
    [
        {"max_completion_tokens": 0},
        {"max_completion_tokens": True},
        {"arrival_ns": -1},
        {"prompt_length": 3},
        {"prompt_tokens": None},
        {"prompt_token_hash": "a" * 64},
        {"prompt_tokens": [101, 102]},
        {"unregistered_feature": "bad"},
    ],
)
def test_request_rejects_bad_data(updates: dict[str, object]) -> None:
    with pytest.raises(ValidationError):
        change(demo_request(), **updates)


def test_hash_only_prompt_is_not_missing_or_zero_length() -> None:
    request = change(demo_request(), prompt_tokens=None, prompt_token_hash="a" * 64)
    assert request.prompt_length == 2 and request.prompt_tokens is None
    assert RequestRecord.model_validate_json(request.model_dump_json()) == request


def test_trace_tracks_arrival_order_and_all_offered_requests() -> None:
    a, b = demo_request("a", 0), demo_request("b", 1)
    trace = TraceRecord(trace_id=a.trace_id, requests=(a, b), provenance="synthetic")
    for bad in ((a, a), (b, a)):
        with pytest.raises(ValidationError):
            change(trace, requests=bad)
    assert trace.digest() != change(trace, requests=(a,)).digest()


def test_action_semantics() -> None:
    with pytest.raises(ValidationError):
        Action(kind="omit", candidate_request_id="r", worker_id="w")
    with pytest.raises(ValidationError):
        Action(kind="admit", candidate_request_id="r", worker_id=None)


def test_missing_observations_are_explicit_and_freshness_measured() -> None:
    observation = Observation[int](
        value=None,
        provenance="missing",
        observed_at_ns=5,
        source="unavailable",
    )
    assert observation.age_ns(12) == 7
    with pytest.raises(ValueError, match="future"):
        observation.age_ns(4)
    with pytest.raises(ValidationError):
        change(observation, value=0)


def test_one_token_tpot_is_undefined() -> None:
    outcome = RequestOutcome(
        request_id="one",
        status="completed",
        reason="demo",
        generated_tokens=1,
        ttft_ns=10,
        tpot_ns=None,
    )
    with pytest.raises(ValidationError, match="TPOT"):
        change(outcome, tpot_ns=0)
    with pytest.raises(ValidationError):
        change(outcome, generated_tokens=2)


def test_noncompletion_cannot_pretend_to_deliver_zero_tokens() -> None:
    with pytest.raises(ValidationError):
        RequestOutcome(
            request_id="r",
            status="rejected",
            reason="capacity",
            generated_tokens=0,
            ttft_ns=None,
            tpot_ns=None,
        )


def test_stable_content_hash_includes_values() -> None:
    assert content_hash({"b": 2, "a": 1}) == content_hash({"a": 1, "b": 2})
    assert content_hash({"a": 1}) != content_hash({"a": 2})
