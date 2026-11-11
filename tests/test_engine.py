from hypothesis import given, settings
from hypothesis import strategies as st

from pigouj.engine_adapter import EngineAdapter, MockEngineAdapter
from pigouj.harness import demo_request
from pigouj.routing import attempt_once


def test_native_mock_authority_after_positive_advice() -> None:
    engine = MockEngineAdapter(capacity=3)
    request = demo_request()
    snapshot = engine.observe_state(5)
    assert engine.can_attempt_admission(request) is True
    # Competing state change after advice makes the original snapshot stale.
    competing = demo_request("competitor")
    assert attempt_once(engine, competing, snapshot).accepted
    result = attempt_once(engine, request, snapshot)
    assert not result.accepted and result.reason == "stale_epoch"
    fresh = engine.observe_state(5)
    result = attempt_once(engine, request, fresh)
    assert not result.accepted and result.reason == "capacity"
    assert engine.observe_state(5) == fresh


def test_explicit_staleness_rejects_without_mutating_state() -> None:
    engine = MockEngineAdapter()
    old = engine.observe_state(5)
    engine.invalidate_snapshot()
    before = engine.observe_state(5)
    result = attempt_once(engine, demo_request(), old)
    assert result.reason == "stale_epoch" and not result.accepted
    assert engine.observe_state(5) == before


def test_mock_protocol_and_missing_gpu_features() -> None:
    engine: EngineAdapter = MockEngineAdapter()
    state = engine.observe_state(0)
    assert state.gpu_identity.provenance == "missing"
    assert state.clock_mhz.value is None
    assert "mock_only" in engine.list_caps()
    assert engine.measure_engine_overhead().provenance == "estimated"


def test_mock_cache_hit_and_miss_are_only_mock_mechanics() -> None:
    engine = MockEngineAdapter(capacity=3)
    assert attempt_once(engine, demo_request("cold", 0), engine.observe_state(0)).accepted
    assert engine.can_attempt_admission(demo_request("second", 0)) is False
    after = engine.observe_state(20)
    assert after.cache_prefix_hashes.value
    assert after.cache_prefix_hashes.provenance == "estimated"
    # Warm exact prompt uses only one mock completion slot.
    for index in range(3):
        request = demo_request(f"warm-{index}", 20)
        assert attempt_once(engine, request, engine.observe_state(20)).accepted
    assert not attempt_once(engine, demo_request("full", 20), engine.observe_state(20)).accepted


def test_batch_occupancy_changes_admission_and_is_in_fingerprint() -> None:
    engine = MockEngineAdapter(capacity=7)
    first = engine.observe_state(0)
    assert attempt_once(engine, demo_request("a", 0), first).accepted
    assert attempt_once(engine, demo_request("b", 0), engine.observe_state(0)).accepted
    state = engine.observe_state(0)
    assert state.active.value is not None and len(state.active.value) == 2
    assert not attempt_once(engine, demo_request("c", 0), state).accepted
    assert first.digest() != state.digest()


@settings(max_examples=60, derandomize=True)
@given(capacity=st.integers(0, 40), lengths=st.lists(st.integers(1, 12), min_size=1, max_size=12))
def test_arbitrary_mock_admission_sequences_respect_capacity(
    capacity: int,
    lengths: list[int],
) -> None:
    engine = MockEngineAdapter(capacity=capacity)
    for index, length in enumerate(lengths):
        before = engine.observe_state(0)
        request = demo_request(str(index), 0, length)
        result = attempt_once(engine, request, before)
        after = engine.observe_state(0)
        assert after.kv_free_blocks.value is not None and after.kv_free_blocks.value >= 0
        if not result.accepted:
            assert before == after
        else:
            assert result.epoch_after == before.epoch + 1
