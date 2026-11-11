"""Read-only preflight. Exit 2 always means the physical gate remains PENDING."""

import argparse
import importlib.metadata
import json
import platform

from pigouj.telemetry import probe_nvml


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--samples", type=int, default=3)
    parser.add_argument("--interval-seconds", type=float, default=0.05)
    parser.add_argument("--gpu-uuid", action="append", default=[])
    args = parser.parse_args()
    report = probe_nvml(
        samples=args.samples,
        interval_seconds=args.interval_seconds,
        device_uuids=tuple(args.gpu_uuid),
    )
    report["platform"] = platform.system()
    try:
        report["vllm_version"] = importlib.metadata.version("vllm")
    except importlib.metadata.PackageNotFoundError:
        report["vllm_version"] = None
    report["pending"] = [
        "native allocator/scheduler events and frontend rejection semantics",
        "engine-consistent freshness; no epoch RPC assumed",
        "declared meter boundary, calibration, aligned clocks and raw event capture",
        "idle/loaded/A-A controls, reproducible replay and instrumentation overhead",
    ]
    print(json.dumps(report, indent=2))
    raise SystemExit(2)


if __name__ == "__main__":
    main()
