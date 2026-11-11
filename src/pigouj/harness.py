"""Two-arm CPU fixture generator. This is NOT a physical label producer.

Energy is assigned an arbitrary demonstration counter, with full-horizon idle
included. Virtual completion ticks are mock mechanics, not engine predictions.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Literal

from pigouj.engine_adapter import MockEngineAdapter
from pigouj.replay import fingerprint, randomized_arm_order
from pigouj.routing import attempt_once
from pigouj.schemas import (
    Action,
    Arm,
    CounterSample,
    EnergyBoundary,
    EnergyMeasurement,
    PairValidation,
    RequestOutcome,
    RequestRecord,
    RunManifest,
    RunRecord,
    SamplingSettings,
    TraceRecord,
    content_hash,
)
from pigouj.validation import validate_pair

Scenario = Literal["accepted", "capacity", "stale_epoch", "censored"]


def implementation_hash() -> str:
    root = Path(__file__).parent
    return content_hash({p.name: p.read_text() for p in sorted(root.glob("*.py"))})


def demo_request(
    request_id: str = "candidate",
    arrival_ns: int = 5,
    max_tokens: int = 1,
    seed: int = 7,
) -> RequestRecord:
    return RequestRecord(
        request_id=request_id,
        trace_id="synthetic-trace",
        session_id="synthetic-session",
        arrival_ns=arrival_ns,
        prompt_length=2,
        prompt_tokens=(101, 102),
        max_completion_tokens=max_tokens,
        sampling=SamplingSettings(temperature=0.0, top_p=1.0, seed=seed),
        model_id="synthetic-model",
        slo_class="demo-no-physical-SLO",
        provenance="synthetic",
    )


def generate_pair(
    scenario: Scenario = "accepted",
    workload_seed: int = 7,
    order_seed: int = 17,
    repeat_id: int = 0,
) -> tuple[RunRecord, RunRecord, PairValidation]:
    order = randomized_arm_order(order_seed, repeat_id)
    prefix = TraceRecord(
        trace_id="synthetic-trace",
        provenance="synthetic",
        requests=(
            demo_request("incumbent-1", 0, 1, workload_seed),
            demo_request("incumbent-2", 1, 3, workload_seed),
        ),
    )
    candidate = demo_request(seed=workload_seed)
    boundary = EnergyBoundary(
        boundary_id="synthetic-demo-boundary",
        kind="SYNTHETIC_CPU_DEMO",
        device_ids=("virtual-worker", "virtual-gateway", "virtual-audit"),
        includes_gateway=True,
        includes_audit=True,
        nonoverlap_verified=False,
        scope_note="Arbitrary simulated counters only; no hardware energy measured",
    )
    pair_id = f"demo-{scenario}-{workload_seed}-{order_seed}-{repeat_id}"
    horizon = 1 if scenario == "censored" else 100
    source_hash = implementation_hash()
    runs: dict[Arm, RunRecord] = {}
    for index, arm in enumerate(order):
        engine = MockEngineAdapter(capacity=8 if scenario == "capacity" else 32)
        prefix_rejections: list[RequestOutcome] = []
        for request in prefix.requests:
            state = engine.observe_state(request.arrival_ns)
            result = attempt_once(engine, request, state)
            if not result.accepted:
                prefix_rejections.append(
                    RequestOutcome(
                        request_id=request.request_id,
                        status="rejected",
                        reason=result.reason,
                        generated_tokens=None,
                        ttft_ns=None,
                        tpot_ns=None,
                    )
                )
        initial = engine.observe_state(candidate.arrival_ns)
        admission = None
        special_outcomes = list(prefix_rejections)
        if arm == "intervention":
            if scenario == "stale_epoch":
                engine.invalidate_snapshot()
            admission = attempt_once(engine, candidate, initial)
            if not admission.accepted:
                special_outcomes.append(
                    RequestOutcome(
                        request_id=candidate.request_id,
                        status="rejected",
                        reason=admission.reason,
                        generated_tokens=None,
                        ttft_ns=None,
                        tpot_ns=None,
                    )
                )
        else:
            special_outcomes.append(
                RequestOutcome(
                    request_id=candidate.request_id,
                    status="omitted",
                    reason="counterfactual_omission",
                    generated_tokens=None,
                    ttft_ns=None,
                    tpot_ns=None,
                )
            )
        drain_elapsed = engine.drain_at_ns - candidate.arrival_ns
        outcomes = engine.outcomes_at(candidate.arrival_ns + horizon) + tuple(special_outcomes)
        # An intentionally arbitrary counter fixture, NOT a physical power model.
        # Same virtual idle/overhead allowance covers the entire common horizon.
        demo_counter_j = 0.01 * horizon + sum(
            float(o.generated_tokens) for o in outcomes if o.generated_tokens is not None
        )
        energy = EnergyMeasurement(
            boundary=boundary,
            meter_id="synthetic-counter-no-hardware",
            status="simulated",
            evidence="synthetic_demonstration",
            source="arbitrary CPU contract fixture",
            start_ns=0,
            end_ns=horizon,
            wall_origin_unix_ns=None,
            samples=(
                CounterSample(elapsed_ns=0, cumulative_j=100.0),
                CounterSample(elapsed_ns=horizon, cumulative_j=100.0 + demo_counter_j),
            ),
            missing_data=False,
            uncertainty_j=0.0,
        )
        manifest = RunManifest(
            run_id=f"{pair_id}-{arm}",
            pair_id=pair_id,
            repeat_id=repeat_id,
            arm=arm,
            arm_order=order,
            execution_index=index,
            workload_seed=workload_seed,
            order_seed=order_seed,
            offered_prefix_hash=prefix.digest(),
            candidate_hash=candidate.digest(),
            initial_fingerprint=fingerprint(initial),
            action=Action(
                kind="omit" if arm == "baseline" else "admit",
                candidate_request_id=candidate.request_id,
                worker_id=None if arm == "baseline" else engine.worker_id,
            ),
            intervention_at_ns=candidate.arrival_ns,
            horizon_ns=horizon,
            cache_policy="warm_prefix_replay",
            estimand="isolated_busy_period_no_future_arrivals",
            engine_version=initial.engine_version,
            engine_commit=initial.engine_commit,
            model_hash=initial.model_hash,
            runtime_config_hash=initial.runtime_config_hash,
            implementation_hash=source_hash,
            boundary=boundary,
            meter_id=energy.meter_id,
            evidence="synthetic_demonstration",
        )
        runs[arm] = RunRecord(
            manifest=manifest,
            offered_prefix=prefix,
            candidate=candidate,
            initial_state=initial,
            admission=admission,
            outcomes=outcomes,
            drained=drain_elapsed <= horizon,
            drain_elapsed_ns=drain_elapsed,
            energy=energy,
        )
    baseline, intervention = runs["baseline"], runs["intervention"]
    return baseline, intervention, validate_pair(baseline, intervention)


def write_demo(output: Path, repeats: int = 2) -> dict[str, object]:
    if repeats < 1:
        raise ValueError("repeats must be positive")
    # Exclusive creation protects existing run evidence from accidental overwrite.
    output.mkdir(parents=True, exist_ok=False)
    verdicts = []
    scenarios: tuple[Scenario, ...] = ("accepted", "capacity", "stale_epoch", "censored")
    with (output / "runs.jsonl").open("x") as runs_file:
        with (output / "pair_ledger.jsonl").open("x") as ledger:
            for scenario in scenarios:
                for repeat in range(repeats):
                    baseline, intervention, verdict = generate_pair(scenario, repeat_id=repeat)
                    for run in sorted(
                        (baseline, intervention), key=lambda r: r.manifest.execution_index
                    ):
                        runs_file.write(run.model_dump_json() + "\n")
                        with (output / f"{run.manifest.run_id}.manifest.json").open("x") as stream:
                            stream.write(run.manifest.model_dump_json(indent=2) + "\n")
                    ledger.write(verdict.model_dump_json() + "\n")
                    verdicts.append(verdict)
    summary: dict[str, object] = {
        "evidence": "synthetic_demonstration",
        "physical_measurements": 0,
        "eligible_for_physical_training": False,
        "pairs": len(verdicts),
        "statuses": {
            status: sum(v.status == status for v in verdicts)
            for status in ("valid", "invalid", "infeasible", "censored")
        },
    }
    with (output / "summary.json").open("x") as stream:
        stream.write(json.dumps(summary, indent=2) + "\n")
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--repeats", type=int, default=2)
    args = parser.parse_args()
    print(json.dumps(write_demo(args.output, args.repeats), sort_keys=True))


if __name__ == "__main__":
    main()
