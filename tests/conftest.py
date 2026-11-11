from pathlib import Path
from typing import TypeVar

import pytest

from pigouj.harness import generate_pair
from pigouj.schemas import Frozen, RunRecord

M = TypeVar("M", bound=Frozen)


def change(model: M, **updates: object) -> M:
    """Construct a validated replacement rather than bypassing validation."""
    return type(model).model_validate({**model.model_dump(), **updates})


@pytest.fixture
def pair() -> tuple[RunRecord, RunRecord]:
    baseline, intervention, verdict = generate_pair()
    assert verdict.status == "valid", verdict.reasons
    return baseline, intervention


@pytest.fixture
def fresh_output(tmp_path: Path) -> Path:
    return tmp_path / "demo"
