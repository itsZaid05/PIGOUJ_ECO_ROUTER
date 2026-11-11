"""Collect a bounded read-only Stage 0 inventory. Never starts CUDA or a model.

Use from repository root: PYTHONPATH=src python3 scripts/phase2_stage0.py --output PATH
An existing output directory is refused. Exit 2 is a pending physical gate.
"""

import argparse
import hashlib
import importlib.metadata
import json
import os
import platform
import subprocess
import sys
import time
from pathlib import Path

from pigouj.telemetry import probe_nvml


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--gpu-uuid", action="append", default=[])
    args = parser.parse_args()
    destination: Path = args.output
    destination.mkdir(parents=True, exist_ok=False)
    commands = (
        ("uname", "-a"),
        ("nvidia-smi", "-L"),
        ("nvidia-smi", "--query-gpu=uuid,name,driver_version,memory.total", "--format=csv"),
        ("nvcc", "--version"),
        ("git", "rev-parse", "HEAD"),
    )
    inventory: list[dict[str, object]] = []
    for command in commands:
        try:
            process = subprocess.run(command, capture_output=True, text=True, timeout=15)
            inventory.append(
                {
                    "argv": command,
                    "exit_code": process.returncode,
                    "stdout": process.stdout,
                    "stderr": process.stderr,
                }
            )
        except (OSError, subprocess.TimeoutExpired) as error:
            inventory.append({"argv": command, "exit_code": None, "error": str(error)})
    packages: dict[str, str | None] = {}
    for name in ("vllm", "torch", "pydantic"):
        try:
            packages[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            packages[name] = None
    # This is public release/source metadata only. It never imports vLLM or torch.
    source_check: dict[str, object] = {"status": "not_installed"}
    if packages["vllm"] is not None:
        distribution = importlib.metadata.distribution("vllm")
        audit = json.loads(Path("artifacts/validation/vllm_api_audit.json").read_text())
        files = []
        for record in audit["files"]:
            path = Path(str(distribution.locate_file(record["path"])))
            digest = hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None
            files.append(
                {
                    "path": record["path"],
                    "installed_sha256": digest,
                    "expected_sha256": record["sha256"],
                    "matches": digest == record["sha256"],
                }
            )
        source_check = {
            "status": "source_match"
            if all(r["matches"] for r in files) and packages["vllm"] == "0.33.0"
            else "source_mismatch",
            "files": files,
            "note": "Python source match only; not proof of compiled CUDA binary provenance",
        }
    selected = tuple(args.gpu_uuid)
    # Inventory without an explicit allocation must not sample other users' boards.
    telemetry = (
        probe_nvml(device_uuids=selected)
        if selected
        else {
            "status": "allocation_uuid_required_before_sampling",
            "physical_gate": "PENDING",
            "eligible_for_physical_training": False,
        }
    )
    summary = {
        "schema_version": "pigouj.stage0.probe.1",
        "physical_gate": "PENDING",
        "training_labels_produced": 0,
        "cuda_workloads_started": 0,
        "wall_unix_ns": time.time_ns(),
        "monotonic_ns": time.monotonic_ns(),
        "python": sys.version,
        "platform": platform.platform(),
        "libc": platform.libc_ver(),
        "allocation": {
            key: os.environ.get(key)
            for key in ("SLURM_JOB_ID", "CUDA_VISIBLE_DEVICES", "NVIDIA_VISIBLE_DEVICES")
        },
        "requested_gpu_uuids": selected,
        "packages": packages,
        "commands": inventory,
        "installed_source_check": source_check,
        "telemetry": telemetry,
        "blocked_on": [
            "native event adapter and calibrated meter",
            "model/tokenizer revision",
            "allocation exclusivity and installation/runtime compatibility",
            "clock/state reproducibility, A/A and overhead acceptance evidence",
        ],
    }
    (destination / "stage0.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps({"output": str(destination), "physical_gate": "PENDING"}))
    raise SystemExit(2)


if __name__ == "__main__":
    main()
