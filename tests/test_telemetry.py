"""CPU failure-path fixtures, never records of real NVIDIA devices."""

import ctypes
from collections.abc import Iterator
from typing import Literal, cast

import pytest

from pigouj.telemetry import probe_nvml


class StubNVML:
    source: Literal["nvml", "test_stub"] = "test_stub"

    def __init__(
        self,
        values: tuple[int | None, ...] = (10, 11, 12),
        code: int | None = 0,
        init_code: int = 0,
    ) -> None:
        self.values: Iterator[int | None] = iter(values)
        self.code, self.init_code = code, init_code
        self.shutdown_calls = 0
        self.energy_reads = 0

    def initialize(self) -> int:
        return self.init_code

    def shutdown(self) -> int:
        self.shutdown_calls += 1
        return 0

    def count(self) -> tuple[int, int | None]:
        return 0, 1

    def handle(self, index: int) -> tuple[int, ctypes.c_void_p]:
        return 0, ctypes.c_void_p(1)

    def identity(self, handle: ctypes.c_void_p, name: str) -> tuple[int, str | None]:
        return 0, "TEST-FIXTURE-NOT-A-GPU"

    def reading(self, handle: ctypes.c_void_p, name: str) -> tuple[int | None, int | None]:
        if name == "power_mw":
            return 0, 123
        self.energy_reads += 1
        return self.code, next(self.values)


def first_device(report: dict[str, object]) -> dict[str, object]:
    return cast(list[dict[str, object]], report["devices"])[0]


@pytest.mark.parametrize(
    ("values", "code", "complete", "reset", "increment"),
    [
        ((10, 11, 12), 0, True, False, True),
        ((0, 0, 0), 0, True, False, False),
        ((12, 11, 13), 0, True, True, False),
        ((None, None, None), 3, False, False, False),
        ((None, None, None), None, False, False, False),
        ((10, None, 12), 0, False, False, False),
    ],
)
def test_probe_preserves_raw_failures_and_never_certifies_physics(
    values: tuple[int | None, ...],
    code: int | None,
    complete: bool,
    reset: bool,
    increment: bool,
) -> None:
    backend = StubNVML(values, code)
    report = probe_nvml(backend, interval_seconds=0.0)
    device = first_device(report)
    assert device["energy_readings_complete"] is complete
    assert device["counter_reset_observed"] is reset
    assert device["counter_increment_observed"] is increment
    readings = cast(list[dict[str, object]], device["raw_readings"])
    assert tuple(r["cumulative_millijoules"] for r in readings) == values
    assert tuple(r["energy_return_code"] for r in readings) == (code,) * 3
    for reading in readings:
        assert cast(int, reading["read_start_monotonic_ns"]) <= cast(
            int, reading["read_end_monotonic_ns"]
        )
    assert report["evidence"] == "test_fixture"
    assert report["physical_gate"] == "PENDING"
    assert report["eligible_for_physical_training"] is False
    assert backend.shutdown_calls == 1


def test_nvml_init_failure_does_not_read_or_shutdown_uninitialized_library() -> None:
    backend = StubNVML(init_code=9)
    report = probe_nvml(backend, interval_seconds=0.0)
    assert report["nvml_init_return_code"] == 9
    assert report["status"] == "initialization_failed"
    assert backend.shutdown_calls == backend.energy_reads == 0


def test_allocation_uuid_filter_prevents_sampling_another_device() -> None:
    backend = StubNVML()
    report = probe_nvml(backend, device_uuids=("ALLOCATED-OTHER-GPU",), interval_seconds=0.0)
    assert backend.energy_reads == 0
    assert first_device(report)["sampling"] == "excluded_by_allocation_uuid"
    assert report["status"] == "allocation_uuid_unavailable"


def test_missing_library_produces_no_fake_readings(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(ctypes.util, "find_library", lambda _: None)
    report = probe_nvml()
    assert report["status"] == "unavailable" and report["evidence"] == "no_readings"
    assert "devices" not in report


@pytest.mark.parametrize(("samples", "interval"), [(1, 0.05), (101, 0.05), (3, -1.0), (3, 1.0)])
def test_probe_rejects_unbounded_sampling_arguments(samples: int, interval: float) -> None:
    with pytest.raises(ValueError):
        probe_nvml(StubNVML(), samples=samples, interval_seconds=interval)
