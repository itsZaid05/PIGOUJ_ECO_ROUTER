"""Read-only NVML probe; no CUDA workload or physical training label path.

Raw millijoules/milliwatts retain return codes and call time brackets. Sensor
availability alone never passes the physical instrumentation gate.
"""

from __future__ import annotations

import ctypes
import ctypes.util
import time
from collections.abc import Callable
from typing import Literal, Protocol, cast


class NVMLBackend(Protocol):
    source: Literal["nvml", "test_stub"]

    def initialize(self) -> int: ...
    def shutdown(self) -> int: ...
    def count(self) -> tuple[int, int | None]: ...
    def handle(self, index: int) -> tuple[int, ctypes.c_void_p]: ...
    def identity(self, handle: ctypes.c_void_p, name: str) -> tuple[int, str | None]: ...
    def reading(self, handle: ctypes.c_void_p, name: str) -> tuple[int | None, int | None]: ...


class CtypesNVML:
    source: Literal["nvml", "test_stub"] = "nvml"

    def __init__(self) -> None:
        library = ctypes.util.find_library("nvidia-ml")
        if library is None:
            raise OSError("no NVML library exposed")
        self.library = ctypes.CDLL(library)

    def _bind(self, name: str, argtypes: list[object]) -> Callable[..., int]:
        function = getattr(self.library, name)
        function.argtypes = argtypes
        function.restype = ctypes.c_int
        return cast(Callable[..., int], function)

    def initialize(self) -> int:
        return self._bind("nvmlInit_v2", [])()

    def shutdown(self) -> int:
        return self._bind("nvmlShutdown", [])()

    def count(self) -> tuple[int, int | None]:
        value = ctypes.c_uint()
        code = self._bind("nvmlDeviceGetCount_v2", [ctypes.POINTER(ctypes.c_uint)])(
            ctypes.byref(value)
        )
        return code, value.value if code == 0 else None

    def handle(self, index: int) -> tuple[int, ctypes.c_void_p]:
        handle = ctypes.c_void_p()
        code = self._bind(
            "nvmlDeviceGetHandleByIndex_v2",
            [
                ctypes.c_uint,
                ctypes.POINTER(ctypes.c_void_p),
            ],
        )(ctypes.c_uint(index), ctypes.byref(handle))
        return code, handle

    def identity(self, handle: ctypes.c_void_p, name: str) -> tuple[int, str | None]:
        functions = {"uuid": "nvmlDeviceGetUUID", "name": "nvmlDeviceGetName"}
        buffer = ctypes.create_string_buffer(128)
        code = self._bind(functions[name], [ctypes.c_void_p, ctypes.c_char_p, ctypes.c_uint])(
            handle,
            buffer,
            ctypes.c_uint(len(buffer)),
        )
        return code, buffer.value.decode(errors="replace") if code == 0 else None

    def reading(self, handle: ctypes.c_void_p, name: str) -> tuple[int | None, int | None]:
        value_type: type[ctypes.c_ulonglong] | type[ctypes.c_uint]
        if name == "energy_mj":
            function_name, value_type = "nvmlDeviceGetTotalEnergyConsumption", ctypes.c_ulonglong
        else:
            function_name, value_type = "nvmlDeviceGetPowerUsage", ctypes.c_uint
        value = value_type()
        try:
            function = self._bind(function_name, [ctypes.c_void_p, ctypes.POINTER(value_type)])
        except AttributeError:
            return None, None
        code = function(handle, ctypes.byref(value))
        return code, value.value if code == 0 else None


def _sample(backend: NVMLBackend, handle: ctypes.c_void_p) -> dict[str, object]:
    before = time.monotonic_ns()
    wall = time.time_ns()
    energy_code, energy = backend.reading(handle, "energy_mj")
    after = time.monotonic_ns()
    power_code, power = backend.reading(handle, "power_mw")
    return {
        "read_start_monotonic_ns": before,
        "read_end_monotonic_ns": after,
        "read_wall_unix_ns": wall,
        "energy_return_code": energy_code,
        "cumulative_millijoules": energy,
        "power_return_code": power_code,
        "instantaneous_milliwatts": power,
    }


def probe_nvml(
    backend: NVMLBackend | None = None,
    *,
    samples: int = 3,
    interval_seconds: float = 0.05,
    device_uuids: tuple[str, ...] = (),
) -> dict[str, object]:
    if not 2 <= samples <= 100:
        raise ValueError("samples must be between 2 and 100")
    if not 0.0 <= interval_seconds <= 0.5:
        raise ValueError("interval must be between 0 and 0.5 seconds")
    report: dict[str, object] = {
        "physical_gate": "PENDING",
        "eligible_for_physical_training": False,
        "requested_samples": samples,
        "requested_interval_seconds": interval_seconds,
        "clock_note": "same-process call brackets, not calibrated cross-device clock alignment",
        "energy_unit_conversion": "1 millijoule = 0.001 joule; raw values retained",
        "boundary": "GPU board diagnostic only; not AC/whole-node energy",
        "requested_device_uuids": device_uuids,
    }
    if backend is None:
        try:
            backend = CtypesNVML()
        except (OSError, AttributeError) as error:
            report.update(status="unavailable", error=str(error), evidence="no_readings")
            return report
    report["source"] = backend.source
    report["evidence"] = "measured_probe" if backend.source == "nvml" else "test_fixture"
    if backend.source == "nvml" and not device_uuids:
        report.update(status="allocation_uuid_required_before_sampling", evidence="no_readings")
        return report
    try:
        init_code = backend.initialize()
    except (OSError, AttributeError) as error:
        report.update(status="unavailable", error=str(error))
        return report
    report["nvml_init_return_code"] = init_code
    if init_code != 0:
        report["status"] = "initialization_failed"
        return report
    try:
        count_code, count = backend.count()
        report.update(device_count_return_code=count_code, device_count=count)
        if count_code != 0 or count is None:
            report["status"] = "enumeration_failed"
            return report
        devices = []
        selected_uuids: set[str] = set()
        for index in range(count):
            handle_code, handle = backend.handle(index)
            device: dict[str, object] = {"index": index, "handle_return_code": handle_code}
            devices.append(device)
            if handle_code != 0:
                continue
            for name in ("uuid", "name"):
                code, value = backend.identity(handle, name)
                device[name] = {"return_code": code, "value": value}
                if name == "uuid":
                    uuid = value
            if device_uuids and uuid not in device_uuids:
                device["sampling"] = "excluded_by_allocation_uuid"
                continue
            if uuid is not None:
                selected_uuids.add(uuid)
            readings = []
            for sample_index in range(samples):
                if sample_index:
                    time.sleep(interval_seconds)
                readings.append(_sample(backend, handle))
            device["raw_readings"] = readings
            values = [r["cumulative_millijoules"] for r in readings]
            valid_values = [v for v in values if isinstance(v, int)]
            complete = len(valid_values) == samples and all(
                r["energy_return_code"] == 0 for r in readings
            )
            monotone = complete and all(
                a <= b
                for a, b in zip(
                    valid_values,
                    valid_values[1:],
                    strict=False,
                )
            )
            device["energy_readings_complete"] = complete
            device["counter_reset_observed"] = complete and not monotone
            device["counter_increment_observed"] = monotone and valid_values[-1] > valid_values[0]
            device["counter_note"] = "no increment over a short probe is inconclusive"
        report.update(devices=devices, status="probe_recorded" if count else "no_devices")
        if set(device_uuids) - selected_uuids:
            report.update(
                status="allocation_uuid_unavailable",
                missing_device_uuids=sorted(set(device_uuids) - selected_uuids),
            )
    except (OSError, AttributeError) as error:
        report.update(status="probe_error", error=str(error))
    finally:
        report["nvml_shutdown_return_code"] = backend.shutdown()
    return report
