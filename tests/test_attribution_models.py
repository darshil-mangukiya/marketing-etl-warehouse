from analytics.attribution_models import (
    normalize_weights,
    position_based_weight,
    time_decay_raw_score,
    u_shaped_weight,
)


def test_u_shaped_weights_sum_to_one_for_three_touchpoints() -> None:
    weights = [
        u_shaped_weight(3, 1, 3),
        u_shaped_weight(3, 2, 2),
        u_shaped_weight(3, 3, 1),
    ]
    assert round(sum(weights), 6) == 1.0
    assert weights == [0.4, 0.2, 0.4]


def test_position_based_weights_sum_to_one_for_four_touchpoints() -> None:
    weights = [
        position_based_weight(4, 1, 4),
        position_based_weight(4, 2, 3),
        position_based_weight(4, 3, 2),
        position_based_weight(4, 4, 1),
    ]
    assert round(sum(weights), 6) == 1.0
    assert weights == [0.3, 0.2, 0.2, 0.3]


def test_time_decay_prefers_recent_touchpoints() -> None:
    weights = normalize_weights([time_decay_raw_score(days) for days in [21, 7, 0]])
    assert round(sum(weights), 6) == 1.0
    assert weights[2] > weights[1] > weights[0]
