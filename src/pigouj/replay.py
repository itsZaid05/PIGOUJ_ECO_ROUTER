"""Exact CPU fingerprint matching; no physical tolerance is assumed."""

import random

from pigouj.schemas import Arm, EngineStateSnapshot, content_hash


def fingerprint(state: EngineStateSnapshot) -> str:
    # Times are relative to replay origin, and remain part of exact matching.
    return state.digest()


def fingerprint_differences(
    left: EngineStateSnapshot,
    right: EngineStateSnapshot,
) -> tuple[str, ...]:
    a, b = left.model_dump(mode="json"), right.model_dump(mode="json")
    return tuple(key for key in a if a[key] != b[key])


def randomized_arm_order(order_seed: int, repeat_id: int) -> tuple[Arm, Arm]:
    seed = int(content_hash((order_seed, repeat_id)), 16)
    order: list[Arm] = ["baseline", "intervention"]
    random.Random(seed).shuffle(order)
    return order[0], order[1]
