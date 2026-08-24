from __future__ import annotations

from math import pow


def u_shaped_weight(touchpoint_count: int, first_touch_rank: int, last_touch_rank: int) -> float:
    if touchpoint_count <= 0:
        return 0.0
    if touchpoint_count == 1:
        return 1.0
    if touchpoint_count == 2:
        return 0.5
    if first_touch_rank == 1 or last_touch_rank == 1:
        return 0.4
    return 0.2 / max(touchpoint_count - 2, 1)


def position_based_weight(touchpoint_count: int, first_touch_rank: int, last_touch_rank: int) -> float:
    if touchpoint_count <= 0:
        return 0.0
    if touchpoint_count == 1:
        return 1.0
    if touchpoint_count == 2:
        return 0.5
    if first_touch_rank == 1:
        return 0.3
    if last_touch_rank == 1:
        return 0.3
    return 0.4 / max(touchpoint_count - 2, 1)


def time_decay_raw_score(days_to_conversion: float, half_life_days: float = 7.0) -> float:
    days = max(float(days_to_conversion), 0.0)
    half_life = max(float(half_life_days), 0.1)
    return pow(0.5, days / half_life)


def normalize_weights(values: list[float]) -> list[float]:
    total = sum(max(value, 0.0) for value in values)
    if total <= 0:
        return [0.0 for _ in values]
    return [max(value, 0.0) / total for value in values]
