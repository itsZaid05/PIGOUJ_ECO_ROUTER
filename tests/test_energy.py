import pytest
from pydantic import ValidationError

from pigouj.energy import InvalidEnergy, counter_energy_j
from pigouj.schemas import CounterSample, RunRecord
from tests.conftest import change


@pytest.mark.parametrize(
    "samples",
    [
        (),
        (CounterSample(elapsed_ns=0, cumulative_j=1.0),),
        (
            CounterSample(elapsed_ns=0, cumulative_j=1.0),
            CounterSample(elapsed_ns=100, cumulative_j=None),
        ),
        (
            CounterSample(elapsed_ns=0, cumulative_j=2.0),
            CounterSample(elapsed_ns=100, cumulative_j=1.0),
        ),
        (
            CounterSample(elapsed_ns=1, cumulative_j=1.0),
            CounterSample(elapsed_ns=100, cumulative_j=2.0),
        ),
        (
            CounterSample(elapsed_ns=0, cumulative_j=1.0),
            CounterSample(elapsed_ns=100, cumulative_j=2.0),
            CounterSample(elapsed_ns=100, cumulative_j=3.0),
        ),
    ],
)
def test_counter_gaps_resets_and_bad_windows_are_invalid(
    pair: tuple[RunRecord, RunRecord],
    samples: tuple[CounterSample, ...],
) -> None:
    with pytest.raises(InvalidEnergy):
        counter_energy_j(change(pair[0].energy, samples=samples))


@pytest.mark.parametrize("value", [float("nan"), float("inf"), -1.0])
def test_counter_rejects_nonphysical_numbers(value: float) -> None:
    with pytest.raises(ValidationError):
        CounterSample(elapsed_ns=0, cumulative_j=value)


def test_boundary_cannot_mix_or_relabel_evidence(pair: tuple[RunRecord, RunRecord]) -> None:
    energy = pair[0].energy
    with pytest.raises(ValidationError):
        change(energy, status="measured", evidence="measured", wall_origin_unix_ns=100)
    with pytest.raises(ValidationError):
        change(energy.boundary, kind="NVML_RAPL_SUBSYSTEM", nonoverlap_verified=False)
    with pytest.raises(ValidationError):
        change(energy, units="mJ")


def test_missing_flag_censors_even_present_endpoints(pair: tuple[RunRecord, RunRecord]) -> None:
    with pytest.raises(InvalidEnergy):
        counter_energy_j(change(pair[0].energy, missing_data=True))
