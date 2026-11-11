"""Read-only preflight, never launches a model or GPU workload.

Exit 2 means the physical integration gate is pending, including on hosts where
NVML works: a meter counter does not verify native admission or replay fidelity.
"""

import ctypes
import ctypes.util
import importlib.metadata
import json
import platform
import time


def main() -> None:
    report: dict[str, object] = {"platform": platform.system(), "physical_gate": "PENDING"}
    try:
        report["vllm_version"] = importlib.metadata.version("vllm")
    except importlib.metadata.PackageNotFoundError:
        report["vllm_version"] = None
    library = ctypes.util.find_library("nvidia-ml")
    report["nvml_library"] = library
    if library is None:
        report["nvml_probe"] = "UNAVAILABLE: no NVML library exposed"
    else:
        nvml = ctypes.CDLL(library)
        rc = nvml.nvmlInit_v2()
        report["nvml_init_return_code"] = rc
        if rc == 0:
            try:
                count = ctypes.c_uint()
                rc = nvml.nvmlDeviceGetCount_v2(ctypes.byref(count))
                report["device_count_return_code"] = rc
                devices = []
                if rc == 0:
                    for index in range(count.value):
                        handle = ctypes.c_void_p()
                        rc = nvml.nvmlDeviceGetHandleByIndex_v2(
                            ctypes.c_uint(index), ctypes.byref(handle)
                        )
                        device: dict[str, object] = {"index": index, "handle_return_code": rc}
                        if rc == 0:
                            for name, function in (
                                ("uuid", "nvmlDeviceGetUUID"),
                                ("name", "nvmlDeviceGetName"),
                            ):
                                buffer = ctypes.create_string_buffer(128)
                                rc = getattr(nvml, function)(handle, buffer, ctypes.c_uint(128))
                                device[name] = (
                                    buffer.value.decode() if rc == 0 else f"NVML_ERROR:{rc}"
                                )
                            readings = []
                            function = getattr(nvml, "nvmlDeviceGetTotalEnergyConsumption", None)
                            if function is None:
                                device["energy_counter"] = "UNAVAILABLE: symbol absent"
                            else:
                                for _ in range(2):
                                    value = ctypes.c_ulonglong()
                                    rc = function(handle, ctypes.byref(value))
                                    readings.append(
                                        {
                                            "monotonic_ns": time.monotonic_ns(),
                                            "return_code": rc,
                                            "cumulative_millijoules": value.value
                                            if rc == 0
                                            else None,
                                        }
                                    )
                                    time.sleep(0.05)
                                device["raw_readings"] = readings
                                device["counter_increment_observed"] = (
                                    all(r["return_code"] == 0 for r in readings)
                                    and readings[1]["cumulative_millijoules"]
                                    > readings[0]["cumulative_millijoules"]
                                )
                        devices.append(device)
                report["devices"] = devices
            finally:
                report["nvml_shutdown_return_code"] = nvml.nvmlShutdown()
    report["pending"] = [
        "native allocator/admission events and rejected-allocation behavior",
        "engine-consistent freshness/epoch semantics; no remote API assumed",
        "PDU or verified subsystem boundary and calibrated clock alignment",
        "idle/loaded meter repeatability, A/A replay and instrumentation overhead",
    ]
    print(json.dumps(report, indent=2))
    raise SystemExit(2)


if __name__ == "__main__":
    main()
