"""Counter-window checks only. No telemetry collection or learned power model."""

from pigouj.schemas import EnergyMeasurement


class InvalidEnergy(ValueError):
    pass


def counter_energy_j(measurement: EnergyMeasurement) -> float:
    samples = measurement.samples
    if measurement.missing_data or len(samples) < 2:
        raise InvalidEnergy("missing counter readings")
    times = tuple(s.elapsed_ns for s in samples)
    if times[0] != measurement.start_ns or times[-1] != measurement.end_ns:
        raise InvalidEnergy("counter readings must cover exact common window")
    if any(a >= b for a, b in zip(times, times[1:], strict=False)):
        raise InvalidEnergy("counter timestamps must strictly increase")
    values = tuple(s.cumulative_j for s in samples)
    if any(v is None for v in values):
        raise InvalidEnergy("missing counter value")
    # Explicitly narrow optional samples; absent data is never converted to zero.
    present = tuple(v for v in values if v is not None)
    if any(a > b for a, b in zip(present, present[1:], strict=False)):
        raise InvalidEnergy("counter reset or rollover; pair must be invalidated")
    return present[-1] - present[0]
