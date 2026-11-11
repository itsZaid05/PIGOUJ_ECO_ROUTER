import json
import sys
from pathlib import Path

import pytest

from scripts import phase2_stage0


def test_stage0_without_allocation_never_samples_nvml(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def forbidden_probe(**_: object) -> dict[str, object]:
        raise AssertionError("no device may be sampled without an explicit allocation UUID")

    monkeypatch.setattr(phase2_stage0, "probe_nvml", forbidden_probe)
    output = tmp_path / "stage0"
    monkeypatch.setattr(sys, "argv", ["stage0", "--output", str(output)])
    with pytest.raises(SystemExit) as pending:
        phase2_stage0.main()
    assert pending.value.code == 2
    report = json.loads((output / "stage0.json").read_text())
    assert report["telemetry"]["status"] == "allocation_uuid_required_before_sampling"
    assert report["physical_gate"] == "PENDING"
    assert report["training_labels_produced"] == report["cuda_workloads_started"] == 0
    commands = [entry["argv"][0] for entry in report["commands"]]
    assert set(commands) == {"uname", "nvidia-smi", "nvcc", "git"}
    with pytest.raises(FileExistsError):
        phase2_stage0.main()
