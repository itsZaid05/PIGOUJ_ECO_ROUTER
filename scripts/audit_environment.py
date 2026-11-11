"""Read-only host probes; missing commands are evidence, not successes."""

import ctypes.util
import importlib.metadata as metadata
import json
import platform
import shutil
import subprocess
from datetime import UTC, datetime
from pathlib import Path

COMMANDS = (
    ("uname", "-a"),
    ("cat", "/etc/os-release"),
    ("lscpu",),
    ("python3", "--version"),
    ("python3", "-m", "pip", "--version"),
    ("codex", "--version"),
    ("git", "--version"),
    ("git", "status", "--short"),
    ("nvcc", "--version"),
    ("nvidia-smi", "-L"),
    ("nvidia-smi", "--query-gpu=uuid,name,driver_version,memory.total", "--format=csv"),
)


def main():
    result = {
        "recorded_at_utc": datetime.now(UTC).isoformat(),
        "platform": platform.platform(),
        "machine": platform.machine(),
        "cwd": str(Path.cwd()),
        "commands": [],
    }
    for command in COMMANDS:
        try:
            p = subprocess.run(command, capture_output=True, text=True, timeout=20)
            record = {
                "argv": command,
                "exit_code": p.returncode,
                "stdout": p.stdout,
                "stderr": p.stderr,
            }
        except (OSError, subprocess.TimeoutExpired) as e:
            record = {"argv": command, "exit_code": None, "error": str(e)}
        result["commands"].append(record)
    result["executables"] = {
        name: shutil.which(name) for name in ("python3", "codex", "git", "uv", "nvcc", "nvidia-smi")
    }
    result["packages"] = {}
    for name in ("vllm", "torch", "nvidia-ml-py", "pydantic", "pytest", "ruff", "mypy"):
        try:
            result["packages"][name] = metadata.version(name)
        except metadata.PackageNotFoundError:
            result["packages"][name] = None
    result["nvidia_devices"] = [str(p) for p in Path("/dev").glob("nvidia*")]
    result["nvidia_proc"] = Path("/proc/driver/nvidia/version").exists()
    result["nvml_library"] = ctypes.util.find_library("nvidia-ml")
    result["rapl_energy_files"] = [str(p) for p in Path("/sys/class/powercap").glob("**/energy_uj")]
    result["repo_files_before_implementation"] = sorted(
        str(p)
        for p in Path(".").rglob("*")
        if p.is_file()
        and not any(part.startswith(".") for part in p.parts)
        and p.parts[0] not in ("work", "artifacts")
    )
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
