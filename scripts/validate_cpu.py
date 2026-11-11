"""Run the bounded CPU gate and retain raw combined stdout/stderr plus exits.

Run from repository root after the documented local venv installation.
The physical probe's exit 2 is an expected pending capability, never a pass.
"""

import argparse
import hashlib
import json
import os
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("artifacts/validation"))
    destination = parser.parse_args().output
    destination.mkdir(parents=True, exist_ok=True)
    commands = (
        ("reference", (".venv/bin/python", "reference/PIGOUJ_math_checks.py", "-v"), 0),
        (
            "unit_tests",
            (".venv/bin/python", "-m", "pytest", "-q", f"--junitxml={destination / 'junit.xml'}"),
            0,
        ),
        ("lint", (".venv/bin/ruff", "check", "src", "tests", "scripts"), 0),
        ("format", (".venv/bin/ruff", "format", "--check", "src", "tests", "scripts"), 0),
        ("types", (".venv/bin/mypy",), 0),
        ("dependencies", (".venv/bin/python", "-m", "pip", "check"), 0),
        (
            "synthetic_demo",
            (
                ".venv/bin/python",
                "-m",
                "pigouj.harness",
                "--output",
                str(destination / "synthetic_demo"),
                "--repeats",
                "2",
            ),
            0,
        ),
        ("physical_pending", (".venv/bin/python", "scripts/probe_physical_capabilities.py"), 2),
    )
    # Existing evidence is retained: a fresh replay target is required for each run.
    if (destination / "synthetic_demo").exists():
        raise SystemExit("Use a fresh checkout/evidence directory; synthetic_demo already exists")
    records = []
    environment = dict(os.environ)
    environment["PIP_CACHE_DIR"] = str(Path("work/pip-cache").resolve())
    for name, command, expected in commands:
        started = datetime.now(UTC).isoformat()
        process = subprocess.run(command, capture_output=True, timeout=120, env=environment)
        output = process.stdout + process.stderr
        log = destination / f"{name}.log"
        log.write_bytes(output)
        record = {
            "name": name,
            "argv": command,
            "started_at_utc": started,
            "exit_code": process.returncode,
            "expected_exit_code": expected,
            "log": str(log),
            "log_sha256": hashlib.sha256(output).hexdigest(),
            "is_physical_pass": False,
        }
        records.append(record)
        print(f"{name}: exit {process.returncode} (expected {expected})", flush=True)
    paths = [Path("pyproject.toml"), Path("requirements-dev.lock")]
    for directory in ("src", "tests", "scripts"):
        paths.extend(sorted(Path(directory).rglob("*.py")))
    source_hashes = {str(path): hashlib.sha256(path.read_bytes()).hexdigest() for path in paths}
    (destination / "validated_source_hashes.json").write_text(
        json.dumps(source_hashes, indent=2) + "\n"
    )
    (destination / "commands.json").write_text(json.dumps(records, indent=2) + "\n")
    good = all(record["exit_code"] == record["expected_exit_code"] for record in records)
    sys.exit(0 if good else 1)


if __name__ == "__main__":
    main()
