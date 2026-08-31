"""Contrat local d'alertes : signaux bornés, fail-closed et sans SLO implicite."""

from __future__ import annotations

import asyncio
import threading
from datetime import datetime, timedelta, timezone, tzinfo
from zoneinfo import ZoneInfo

import pytest

from app.api.routes import health as health_module
from app.core import local_alerts as local_alerts_module
from app.core.local_alerts import (
    AlertSilence,
    LocalAlertEvaluator,
    RULE_IDS,
    SILENCE_REASON_CODES,
    evaluate_local_alerts,
    local_alert_evaluator,
)
from app.core.observability import (
    ProductIntelligenceMetricsRegistry,
    RequestMetricsRegistry,
)


def _stage(
    sample_size: int,
    *,
    generation: int = 1,
    errors: int = 0,
    p95_ms: float | None = None,
) -> dict:
    return {
        "window_kind": "last_events",
        "window_capacity": 512,
        "window_truncated": False,
        "generation": generation,
        "events_seen": sample_size,
        "retained_events": sample_size,
        "sample_size": sample_size,
        "cancelled_excluded": 0,
        "outcomes": {"error": errors, "ok": sample_size - errors},
        "latency_ms": {
            "p95": p95_ms if sample_size else None,
            "sample_size": sample_size,
        },
    }


def _inputs(
    *,
    http_samples: int = 0,
    http_5xx: int = 0,
    catalogue_samples: int = 0,
    catalogue_errors: int = 0,
    retrieval_samples: int = 0,
    retrieval_errors: int = 0,
    retrieval_p95_ms: float | None = None,
    recommendation_samples: int = 0,
    recommendation_timeouts: int = 0,
    generation: int = 1,
) -> dict:
    return {
        "http": {
            "window_kind": "last_events",
            "window_capacity": 512,
            "window_truncated": False,
            "generation": generation,
            "events_seen": http_samples,
            "retained_events": http_samples,
            "sample_size": http_samples,
            "status_groups": {
                "2xx": http_samples - http_5xx,
                "5xx": http_5xx,
            },
        },
        "product_intelligence": {
            "recommendations": {
                "window_kind": "last_events",
                "window_capacity": 512,
                "window_truncated": False,
                "generation": generation,
                "events_seen": recommendation_samples,
                "retained_events": recommendation_samples,
                "sample_size": recommendation_samples,
                "delivery": {
                    "generated": recommendation_samples - recommendation_timeouts,
                    "timeout": recommendation_timeouts,
                },
            },
            "pipeline_stages": {
                "catalogue": _stage(
                    catalogue_samples,
                    generation=generation,
                    errors=catalogue_errors,
                    p95_ms=1.0 if catalogue_samples else None,
                ),
                "retrieval": _stage(
                    retrieval_samples,
                    generation=generation,
                    errors=retrieval_errors,
                    p95_ms=retrieval_p95_ms,
                ),
            },
        },
    }


def _registry_inputs(
    requests: RequestMetricsRegistry,
    product: ProductIntelligenceMetricsRegistry,
) -> dict:
    return {
        "http": requests.alert_snapshot(),
        "product_intelligence": product.alert_snapshot(),
    }


def test_empty_or_short_windows_are_insufficient_data_never_healthy():
    evaluator = LocalAlertEvaluator()

    empty = evaluator.evaluate(_inputs())
    assert empty["overall_state"] == "insufficient_data"
    assert empty["representative_traffic"] is False
    assert empty["policy_status"] == "provisional_local_not_slo"
    assert set(empty["rules"]) == set(RULE_IDS)
    assert all(rule["state"] == "insufficient_data" for rule in empty["rules"].values())

    short = evaluator.evaluate(_inputs(http_samples=99, http_5xx=99))
    rule = short["rules"]["http_5xx_ratio"]
    assert rule["state"] == "insufficient_data"
    assert rule["transition"] == "none"
    assert rule["reason_code"] == "minimum_samples_not_met"
    assert rule["sample_size"] == 99
    assert rule["value"] == 1.0


def test_http_rule_triggers_on_boundary_uses_hysteresis_and_resolves():
    evaluator = LocalAlertEvaluator()

    triggered = evaluator.evaluate(_inputs(http_samples=100, http_5xx=5))
    rule = triggered["rules"]["http_5xx_ratio"]
    assert rule["state"] == "firing"
    assert rule["transition"] == "triggered"
    assert rule["notification"]["state"] == "notify"

    deadband = evaluator.evaluate(_inputs(http_samples=167, http_5xx=5))
    rule = deadband["rules"]["http_5xx_ratio"]
    assert rule["state"] == "firing"
    assert rule["transition"] == "none"
    assert rule["notification"]["state"] == "inactive"

    resolved = evaluator.evaluate(_inputs(http_samples=250, http_5xx=5))
    rule = resolved["rules"]["http_5xx_ratio"]
    assert rule["state"] == "not_firing_provisional"
    assert rule["transition"] == "resolved"
    assert resolved["overall_state"] == "insufficient_data"


def test_displayed_ratio_precision_cannot_contradict_resolution_threshold():
    evaluator = LocalAlertEvaluator()
    evaluator.evaluate(_inputs(http_samples=100, http_5xx=5))

    just_above_resolution = evaluator.evaluate(
        _inputs(http_samples=499, http_5xx=10)
    )["rules"]["http_5xx_ratio"]
    assert just_above_resolution["state"] == "firing"
    assert just_above_resolution["value"] == 0.02004
    assert just_above_resolution["value"] > just_above_resolution["threshold"][
        "resolve_lte"
    ]

    at_resolution = evaluator.evaluate(_inputs(http_samples=500, http_5xx=10))[
        "rules"
    ]["http_5xx_ratio"]
    assert at_resolution["value"] == 0.02
    assert at_resolution["transition"] == "resolved"


def test_stage_timeout_and_latency_rules_use_only_their_fixed_sources():
    evaluated = LocalAlertEvaluator().evaluate(
        _inputs(
            catalogue_samples=50,
            catalogue_errors=5,
            retrieval_samples=200,
            retrieval_errors=20,
            retrieval_p95_ms=750.0,
            recommendation_samples=100,
            recommendation_timeouts=5,
        )
    )

    assert evaluated["rules"]["catalogue_error_ratio"]["state"] == "firing"
    assert evaluated["rules"]["retrieval_error_ratio"]["state"] == "firing"
    assert evaluated["rules"]["assistant_timeout_ratio"]["state"] == "firing"
    assert evaluated["rules"]["retrieval_p95_ms"]["state"] == "firing"


@pytest.mark.parametrize(
    ("inputs", "expected_rule"),
    [
        (
            _inputs(catalogue_samples=50, catalogue_errors=5),
            "catalogue_error_ratio",
        ),
        (
            _inputs(
                retrieval_samples=50,
                retrieval_errors=5,
                retrieval_p95_ms=1.0,
            ),
            "retrieval_error_ratio",
        ),
        (
            _inputs(recommendation_samples=100, recommendation_timeouts=5),
            "assistant_timeout_ratio",
        ),
        (
            _inputs(
                retrieval_samples=200,
                retrieval_errors=0,
                retrieval_p95_ms=750.0,
            ),
            "retrieval_p95_ms",
        ),
    ],
)
def test_each_product_rule_has_a_one_hot_source(inputs, expected_rule):
    evaluated = LocalAlertEvaluator().evaluate(inputs)
    product_rule_ids = {
        "catalogue_error_ratio",
        "retrieval_error_ratio",
        "assistant_timeout_ratio",
        "retrieval_p95_ms",
    }
    firing = {
        rule_id
        for rule_id in product_rule_ids
        if evaluated["rules"][rule_id]["state"] == "firing"
    }
    assert firing == {expected_rule}


def test_retrieval_latency_hysteresis_is_independent_from_scrape_count():
    requests = RequestMetricsRegistry()
    product = ProductIntelligenceMetricsRegistry()
    evaluator = LocalAlertEvaluator()

    for _index in range(200):
        product.record_stage(stage="retrieval", outcome="ok", elapsed_ms=750.0)
    inputs = {
        "http": requests.alert_snapshot(),
        "product_intelligence": product.alert_snapshot(),
    }
    first = evaluator.evaluate(inputs)
    assert first["rules"]["retrieval_p95_ms"]["transition"] == "triggered"

    duplicate = evaluator.evaluate(inputs)
    assert duplicate["rules"]["retrieval_p95_ms"]["state"] == "firing"
    assert duplicate["rules"]["retrieval_p95_ms"]["transition"] == "none"
    assert duplicate["rules"]["retrieval_p95_ms"]["notification"]["state"] == "inactive"

    for _index in range(488):
        product.record_stage(stage="retrieval", outcome="ok", elapsed_ms=650.0)
    repeated = evaluator.evaluate(
        {
            "http": requests.alert_snapshot(),
            "product_intelligence": product.alert_snapshot(),
        }
    )
    assert repeated["rules"]["retrieval_p95_ms"]["state"] == "firing"
    assert repeated["rules"]["retrieval_p95_ms"]["transition"] == "none"

    for _index in range(512):
        product.record_stage(stage="retrieval", outcome="ok", elapsed_ms=600.0)
    recovered = evaluator.evaluate(
        {
            "http": requests.alert_snapshot(),
            "product_intelligence": product.alert_snapshot(),
        }
    )
    assert recovered["rules"]["retrieval_p95_ms"]["transition"] == "resolved"


def test_silence_never_hides_state_expires_and_is_strictly_bounded():
    now = datetime(2026, 8, 29, tzinfo=timezone.utc)
    silence = AlertSilence(
        rule_id="http_5xx_ratio",
        reason_code="controlled_test",
        created_at=now,
        expires_at=now + timedelta(minutes=30),
    )
    evaluator = LocalAlertEvaluator()

    silenced = evaluator.evaluate(
        _inputs(http_samples=100, http_5xx=5),
        silences=(silence,),
        now=now,
    )
    rule = silenced["rules"]["http_5xx_ratio"]
    assert rule["state"] == "firing"
    assert rule["notification"] == {
        "state": "silenced",
        "reason_code": "controlled_test",
        "until": "2026-08-29T00:30:00Z",
    }

    expired = evaluator.evaluate(
        _inputs(http_samples=100, http_5xx=5),
        silences=(silence,),
        now=now + timedelta(minutes=31),
    )
    assert expired["rules"]["http_5xx_ratio"]["notification"]["state"] == "inactive"

    fresh_after_expiry = evaluator.evaluate(
        _inputs(http_samples=101, http_5xx=5),
        silences=(silence,),
        now=now + timedelta(minutes=31),
    )
    assert fresh_after_expiry["rules"]["http_5xx_ratio"]["notification"][
        "state"
    ] == "notify"

    duplicate_after_notification = evaluator.evaluate(
        _inputs(http_samples=101, http_5xx=5),
        silences=(silence,),
        now=now + timedelta(minutes=31),
    )
    assert duplicate_after_notification["rules"]["http_5xx_ratio"][
        "notification"
    ]["state"] == "inactive"

    for invalid in (
        AlertSilence("unknown", "controlled_test", now, now + timedelta(minutes=1)),
        AlertSilence("http_5xx_ratio", "free_text", now, now + timedelta(minutes=1)),
        AlertSilence("http_5xx_ratio", "maintenance", now, now + timedelta(hours=2)),
    ):
        with pytest.raises(ValueError):
            LocalAlertEvaluator().evaluate(_inputs(), silences=(invalid,), now=now)


def test_recovery_during_silence_is_visible_and_not_notified():
    now = datetime(2026, 8, 29, tzinfo=timezone.utc)
    silence = AlertSilence(
        "http_5xx_ratio",
        "maintenance",
        now,
        now + timedelta(minutes=10),
    )
    evaluator = LocalAlertEvaluator()
    evaluator.evaluate(
        _inputs(http_samples=100, http_5xx=5),
        silences=(silence,),
        now=now,
    )

    recovered = evaluator.evaluate(
        _inputs(http_samples=250, http_5xx=5),
        silences=(silence,),
        now=now + timedelta(minutes=1),
    )["rules"]["http_5xx_ratio"]
    assert recovered["state"] == "not_firing_provisional"
    assert recovered["transition"] == "resolved"
    assert recovered["notification"]["state"] == "inactive"


def test_bounded_event_window_evicts_old_errors_and_can_resolve():
    requests = RequestMetricsRegistry()
    product = ProductIntelligenceMetricsRegistry()
    evaluator = LocalAlertEvaluator()

    for index in range(100):
        requests.record(
            method="GET",
            route="/fixed-template",
            status_code=500 if index < 5 else 200,
            elapsed_ms=1,
        )
    first = evaluator.evaluate(
        {
            "http": requests.alert_snapshot(),
            "product_intelligence": product.alert_snapshot(),
        }
    )
    assert first["rules"]["http_5xx_ratio"]["state"] == "firing"

    for _index in range(512):
        requests.record(
            method="GET",
            route="/fixed-template",
            status_code=200,
            elapsed_ms=1,
        )
    second = evaluator.evaluate(
        {
            "http": requests.alert_snapshot(),
            "product_intelligence": product.alert_snapshot(),
        }
    )
    assert second["rules"]["http_5xx_ratio"]["transition"] == "resolved"
    assert second["rules"]["http_5xx_ratio"]["window_truncated"] is True


def test_cancellation_dominated_window_is_insufficient_not_a_false_green():
    registry = ProductIntelligenceMetricsRegistry()
    for _index in range(50):
        registry.record_stage(stage="retrieval", outcome="ok", elapsed_ms=500)
    for _index in range(100):
        registry.record_stage(stage="retrieval", outcome="cancelled", elapsed_ms=1)

    snapshot = registry.alert_snapshot()["pipeline_stages"]["retrieval"]
    assert snapshot["sample_size"] == 50
    assert snapshot["cancelled_excluded"] == 100
    assert snapshot["outcomes"] == {"ok": 50}
    evaluated = LocalAlertEvaluator().evaluate(
        {
            "http": RequestMetricsRegistry().alert_snapshot(),
            "product_intelligence": registry.alert_snapshot(),
        }
    )
    rule = evaluated["rules"]["retrieval_error_ratio"]
    assert rule["state"] == "insufficient_data"
    assert rule["reason_code"] == "insufficient_observable_events"


def test_manifest_error_breach_still_fires_when_cancellations_dominate():
    registry = ProductIntelligenceMetricsRegistry()
    for _index in range(50):
        registry.record_stage(stage="retrieval", outcome="error", elapsed_ms=500)
    for _index in range(100):
        registry.record_stage(stage="retrieval", outcome="cancelled", elapsed_ms=1)

    evaluated = LocalAlertEvaluator().evaluate(
        {
            "http": RequestMetricsRegistry().alert_snapshot(),
            "product_intelligence": registry.alert_snapshot(),
        }
    )

    rule = evaluated["rules"]["retrieval_error_ratio"]
    assert rule["state"] == "firing"
    assert rule["transition"] == "triggered"
    assert rule["sample_size"] == 50
    assert rule["value"] == 1.0


def test_untrusted_http_methods_share_one_bounded_series():
    registry = RequestMetricsRegistry()
    for index in range(1_000):
        registry.record(
            method=f"UNTRUSTED-{index}",
            route="/fixed-template",
            status_code=200,
            elapsed_ms=1,
        )

    routes = registry.snapshot()["routes"]
    assert list(routes) == ["OTHER_METHOD /fixed-template"]
    assert routes["OTHER_METHOD /fixed-template"]["requests"] == 1_000


def test_invalid_status_codes_are_bounded_and_fail_closed_for_alerts():
    registry = RequestMetricsRegistry()
    for status_code in (*range(-10_000, 10_000, 100), True):
        registry.record(
            method="GET",
            route="/fixed-template",
            status_code=status_code,
            elapsed_ms=1,
        )

    alert_input = registry.alert_snapshot()
    assert set(alert_input["status_groups"]) == {"1xx", "2xx", "3xx", "4xx", "5xx", "OTHER_STATUS"}
    evaluated = LocalAlertEvaluator().evaluate(
        {
            "http": alert_input,
            "product_intelligence": ProductIntelligenceMetricsRegistry().alert_snapshot(),
        }
    )
    rule = evaluated["rules"]["http_5xx_ratio"]
    assert rule["state"] == "insufficient_data"
    assert rule["reason_code"] == "invalid_aggregate"


def test_malformed_or_secret_input_fails_closed_without_echoing_it():
    inputs = _inputs(http_samples=100, http_5xx=5)
    inputs["query"] = "private-query-123"
    inputs["http"]["status_groups"] = {"5xx": float("nan")}
    inputs["product_intelligence"]["payload"] = "private-offer-456"

    evaluated = LocalAlertEvaluator().evaluate(inputs)

    rule = evaluated["rules"]["http_5xx_ratio"]
    assert rule["state"] == "insufficient_data"
    assert rule["reason_code"] == "invalid_aggregate"
    serialized = repr(evaluated)
    assert "private-query-123" not in serialized
    assert "private-offer-456" not in serialized
    assert len(evaluated["rules"]) == len(RULE_IDS) == 5


def test_window_contract_unknown_counters_and_partial_latency_fail_closed():
    wrong_window = _inputs(http_samples=100)
    wrong_window["http"].update(
        {"window_kind": "all_time", "window_capacity": 1}
    )
    wrong_counter = _inputs(http_samples=100)
    wrong_counter["http"]["status_groups"] = {"future_server_failure": 100}
    partial_latency = _inputs(retrieval_samples=200, retrieval_p95_ms=500)
    partial_latency["product_intelligence"]["pipeline_stages"]["retrieval"][
        "latency_ms"
    ]["sample_size"] = 199

    evaluator = LocalAlertEvaluator()
    assert evaluator.evaluate(wrong_window)["rules"]["http_5xx_ratio"][
        "reason_code"
    ] == "invalid_aggregate"
    assert evaluator.evaluate(wrong_counter)["rules"]["http_5xx_ratio"][
        "reason_code"
    ] == "invalid_aggregate"
    assert evaluator.evaluate(partial_latency)["rules"]["retrieval_p95_ms"][
        "reason_code"
    ] == "invalid_aggregate"


def test_corrected_invalid_aggregate_at_same_position_can_trigger_once():
    evaluator = LocalAlertEvaluator()
    invalid = _inputs(http_samples=100, http_5xx=5)
    invalid["http"]["status_groups"] = "invalid"

    rejected = evaluator.evaluate(invalid)["rules"]["http_5xx_ratio"]
    assert rejected["state"] == "insufficient_data"
    assert rejected["reason_code"] == "invalid_aggregate"
    assert rejected["generation"] == 1
    assert rejected["events_seen"] == 100

    corrected = evaluator.evaluate(_inputs(http_samples=100, http_5xx=5))[
        "rules"
    ]["http_5xx_ratio"]
    assert corrected["state"] == "firing"
    assert corrected["transition"] == "triggered"

    duplicate = evaluator.evaluate(_inputs(http_samples=100, http_5xx=5))[
        "rules"
    ]["http_5xx_ratio"]
    assert duplicate["transition"] == "none"
    assert duplicate["notification"]["state"] == "inactive"


def test_newer_invalid_aggregate_advances_watermark_and_blocks_older_replay():
    requests = RequestMetricsRegistry()
    product = ProductIntelligenceMetricsRegistry()
    evaluator = LocalAlertEvaluator()
    for index in range(100):
        requests.record(
            method="GET",
            route="/fixed-template",
            status_code=500 if index < 5 else 200,
            elapsed_ms=1,
        )
    evaluator.evaluate(_registry_inputs(requests, product))

    for _index in range(150):
        requests.record(
            method="GET",
            route="/fixed-template",
            status_code=200,
            elapsed_ms=1,
        )
    older_recovery = requests.alert_snapshot()
    for _index in range(50):
        requests.record(
            method="GET",
            route="/fixed-template",
            status_code=200,
            elapsed_ms=1,
        )
    newer_invalid = requests.alert_snapshot()
    newer_invalid["status_groups"] = "invalid"

    rejected = evaluator.evaluate(
        {
            "http": newer_invalid,
            "product_intelligence": product.alert_snapshot(),
        }
    )["rules"]["http_5xx_ratio"]
    assert rejected["reason_code"] == "invalid_aggregate"
    assert rejected["events_seen"] == 300

    replayed = evaluator.evaluate(
        {
            "http": older_recovery,
            "product_intelligence": product.alert_snapshot(),
        }
    )["rules"]["http_5xx_ratio"]
    assert replayed["state"] == "insufficient_data"
    assert replayed["reason_code"] == "stale_snapshot"

    requests.record(
        method="GET",
        route="/fixed-template",
        status_code=200,
        elapsed_ms=1,
    )
    resolved = evaluator.evaluate(_registry_inputs(requests, product))["rules"][
        "http_5xx_ratio"
    ]
    assert resolved["transition"] == "resolved"


def test_conflicting_content_at_same_position_is_fail_closed():
    evaluator = LocalAlertEvaluator()
    accepted = evaluator.evaluate(_inputs(http_samples=100, http_5xx=0))["rules"][
        "http_5xx_ratio"
    ]
    assert accepted["state"] == "not_firing_provisional"

    conflict = evaluator.evaluate(_inputs(http_samples=100, http_5xx=5))["rules"][
        "http_5xx_ratio"
    ]
    assert conflict["state"] == "insufficient_data"
    assert conflict["reason_code"] == "conflicting_snapshot"
    assert conflict["value"] == conflict["threshold"]["trigger_gte"]

    fresh = evaluator.evaluate(_inputs(http_samples=106, http_5xx=6))["rules"][
        "http_5xx_ratio"
    ]
    assert fresh["state"] == "firing"
    assert fresh["transition"] == "triggered"


def test_insufficient_data_keeps_firing_latch_until_a_real_resolution():
    evaluator = LocalAlertEvaluator()
    evaluator.evaluate(_inputs(http_samples=100, http_5xx=5))

    insufficient = evaluator.evaluate(_inputs(generation=2))
    assert insufficient["rules"]["http_5xx_ratio"]["state"] == "insufficient_data"
    assert insufficient["rules"]["http_5xx_ratio"]["reason_code"] == (
        "minimum_samples_not_met"
    )

    deadband = evaluator.evaluate(
        _inputs(http_samples=167, http_5xx=5, generation=2)
    )
    assert deadband["rules"]["http_5xx_ratio"]["state"] == "firing"
    assert deadband["rules"]["http_5xx_ratio"]["transition"] == "none"

    resolved = evaluator.evaluate(
        _inputs(http_samples=250, http_5xx=5, generation=2)
    )
    assert resolved["rules"]["http_5xx_ratio"]["transition"] == "resolved"


def test_registry_generation_distinguishes_an_equal_sequence_after_reset():
    requests = RequestMetricsRegistry()
    product = ProductIntelligenceMetricsRegistry()
    evaluator = LocalAlertEvaluator()

    for _index in range(100):
        requests.record(
            method="GET",
            route="/fixed-template",
            status_code=200,
            elapsed_ms=1,
        )
    before_reset = requests.alert_snapshot()
    assert evaluator.evaluate(_registry_inputs(requests, product))["rules"][
        "http_5xx_ratio"
    ]["state"] == "not_firing_provisional"

    requests.reset()
    for index in range(100):
        requests.record(
            method="GET",
            route="/fixed-template",
            status_code=500 if index < 5 else 200,
            elapsed_ms=1,
        )
    after_reset = requests.alert_snapshot()
    assert after_reset["events_seen"] == before_reset["events_seen"] == 100
    assert after_reset["generation"] == before_reset["generation"] + 1

    rule = evaluator.evaluate(_registry_inputs(requests, product))["rules"][
        "http_5xx_ratio"
    ]
    assert rule["state"] == "firing"
    assert rule["transition"] == "triggered"


def test_replayed_older_snapshot_is_stale_and_cannot_resolve_a_latch():
    requests = RequestMetricsRegistry()
    product = ProductIntelligenceMetricsRegistry()
    evaluator = LocalAlertEvaluator()

    for _index in range(100):
        requests.record(
            method="GET",
            route="/fixed-template",
            status_code=200,
            elapsed_ms=1,
        )
    old_http = requests.alert_snapshot()
    evaluator.evaluate(
        {"http": old_http, "product_intelligence": product.alert_snapshot()}
    )

    for _index in range(6):
        requests.record(
            method="GET",
            route="/fixed-template",
            status_code=500,
            elapsed_ms=1,
        )
    triggered = evaluator.evaluate(_registry_inputs(requests, product))
    assert triggered["rules"]["http_5xx_ratio"]["transition"] == "triggered"

    replayed = evaluator.evaluate(
        {"http": old_http, "product_intelligence": product.alert_snapshot()}
    )["rules"]["http_5xx_ratio"]
    assert replayed["state"] == "insufficient_data"
    assert replayed["transition"] == "none"
    assert replayed["reason_code"] == "stale_snapshot"
    assert replayed["generation"] == old_http["generation"]
    assert replayed["events_seen"] == old_http["events_seen"] == 100

    requests.record(
        method="GET",
        route="/fixed-template",
        status_code=200,
        elapsed_ms=1,
    )
    fresh = evaluator.evaluate(_registry_inputs(requests, product))["rules"][
        "http_5xx_ratio"
    ]
    assert fresh["state"] == "firing"
    assert fresh["transition"] == "none"


def test_evaluator_reset_clears_latches_positions_and_notification_dedupe():
    inputs = _inputs(http_samples=100, http_5xx=5)
    evaluator = LocalAlertEvaluator()

    first = evaluator.evaluate(inputs)["rules"]["http_5xx_ratio"]
    duplicate = evaluator.evaluate(inputs)["rules"]["http_5xx_ratio"]
    assert first["transition"] == "triggered"
    assert duplicate["notification"]["state"] == "inactive"

    evaluator.reset()
    rearmed = evaluator.evaluate(inputs)["rules"]["http_5xx_ratio"]
    assert rearmed["transition"] == "triggered"
    assert rearmed["notification"]["state"] == "notify"


def test_registry_reset_clears_windows_increments_generation_and_truncation():
    requests = RequestMetricsRegistry()
    product = ProductIntelligenceMetricsRegistry()
    for _index in range(513):
        requests.record(
            method="GET",
            route="/fixed-template",
            status_code=200,
            elapsed_ms=1,
        )
        product.record_recommendation({"cards": [], "real": False}, delivery="cache")
        product.record_stage(stage="retrieval", outcome="ok", elapsed_ms=1)

    request_before = requests.alert_snapshot()
    product_before = product.alert_snapshot()
    assert request_before["retained_events"] == 512
    assert request_before["window_truncated"] is True
    assert product_before["recommendations"]["window_truncated"] is True
    assert product_before["pipeline_stages"]["retrieval"]["window_truncated"] is True

    requests.reset()
    product.reset()
    request_after = requests.alert_snapshot()
    product_after = product.alert_snapshot()
    assert request_after["generation"] == request_before["generation"] + 1
    assert request_after["events_seen"] == request_after["retained_events"] == 0
    assert request_after["window_truncated"] is False
    assert product_after["recommendations"]["generation"] == (
        product_before["recommendations"]["generation"] + 1
    )
    assert product_after["recommendations"]["events_seen"] == 0
    assert product_after["pipeline_stages"] == {}

    product.record_stage(stage="retrieval", outcome="ok", elapsed_ms=1)
    stage_after = product.alert_snapshot()["pipeline_stages"]["retrieval"]
    assert stage_after["generation"] == product_after["recommendations"]["generation"]
    assert stage_after["events_seen"] == 1


def test_silence_duration_is_computed_in_utc_across_daylight_saving_fold():
    brussels = ZoneInfo("Europe/Brussels")
    created_at = datetime(2026, 10, 25, 2, 0, tzinfo=brussels, fold=0)
    expires_at = datetime(2026, 10, 25, 2, 59, tzinfo=brussels, fold=1)
    silence = AlertSilence(
        "http_5xx_ratio",
        "maintenance",
        created_at,
        expires_at,
    )

    with pytest.raises(ValueError, match="invalid_silence_duration"):
        LocalAlertEvaluator().evaluate(
            _inputs(),
            silences=(silence,),
            now=created_at,
        )


def test_timezone_object_without_utc_offset_is_rejected_as_naive():
    class MissingOffset(tzinfo):
        def utcoffset(self, _value):
            return None

        def dst(self, _value):
            return None

    pseudo_aware = datetime(2026, 8, 29, tzinfo=MissingOffset())
    valid_now = datetime(2026, 8, 29, tzinfo=timezone.utc)

    with pytest.raises(ValueError, match="evaluation_requires_timezone"):
        LocalAlertEvaluator().evaluate(_inputs(), now=pseudo_aware)

    silence = AlertSilence(
        "http_5xx_ratio",
        "maintenance",
        pseudo_aware,
        pseudo_aware + timedelta(minutes=1),
    )
    with pytest.raises(ValueError, match="silence_requires_timezone"):
        LocalAlertEvaluator().evaluate(
            _inputs(),
            silences=(silence,),
            now=valid_now,
        )


@pytest.mark.parametrize("invalid_now", [False, 0, "", {}])
def test_falsy_invalid_evaluation_time_is_never_replaced_by_wall_clock(invalid_now):
    with pytest.raises(ValueError, match="evaluation_requires_timezone"):
        LocalAlertEvaluator().evaluate(_inputs(), now=invalid_now)


def test_silence_reason_registry_is_immutable():
    assert isinstance(SILENCE_REASON_CODES, frozenset)
    with pytest.raises(AttributeError):
        SILENCE_REASON_CODES.add("private-free-text")  # type: ignore[attr-defined]


def test_silence_accepts_exactly_one_hour_and_rejects_unsafe_boundaries():
    now = datetime(2026, 8, 29, tzinfo=timezone.utc)
    exact = AlertSilence(
        "http_5xx_ratio",
        "maintenance",
        now,
        now + timedelta(hours=1),
    )
    evaluated = LocalAlertEvaluator().evaluate(
        _inputs(http_samples=100, http_5xx=5),
        silences=(exact,),
        now=now,
    )
    assert evaluated["rules"]["http_5xx_ratio"]["notification"]["state"] == "silenced"

    invalid_sets = (
        (AlertSilence("http_5xx_ratio", "maintenance", now, now),),
        (
            AlertSilence(
                "http_5xx_ratio",
                "maintenance",
                now.replace(tzinfo=None),
                (now + timedelta(minutes=1)).replace(tzinfo=None),
            ),
        ),
        (exact, exact),
    )
    for invalid in invalid_sets:
        with pytest.raises(ValueError):
            LocalAlertEvaluator().evaluate(
                _inputs(),
                silences=invalid,
                now=now,
            )

    with pytest.raises(ValueError, match="evaluation_requires_timezone"):
        LocalAlertEvaluator().evaluate(_inputs(), now=now.replace(tzinfo=None))


def test_silence_iterators_are_materialized_outside_the_state_lock():
    now = datetime(2026, 8, 29, tzinfo=timezone.utc)
    evaluator = LocalAlertEvaluator()
    completed: list[dict] = []
    failures: list[BaseException] = []

    def silences():
        evaluator.reset()
        yield AlertSilence(
            "http_5xx_ratio",
            "controlled_test",
            now,
            now + timedelta(minutes=1),
        )

    def run() -> None:
        try:
            completed.append(
                evaluator.evaluate(
                    _inputs(http_samples=100, http_5xx=5),
                    silences=silences(),
                    now=now,
                )
            )
        except BaseException as exc:  # pragma: no cover - assertion relay
            failures.append(exc)

    worker = threading.Thread(target=run, daemon=True)
    worker.start()
    worker.join(timeout=2)

    assert not worker.is_alive(), "silence iterator ran under evaluator state lock"
    assert not failures
    assert completed[0]["rules"]["http_5xx_ratio"]["notification"]["state"] == "silenced"


def test_input_mappings_are_read_outside_the_state_lock():
    evaluator = LocalAlertEvaluator()
    completed: list[dict] = []
    failures: list[BaseException] = []

    class ReentrantInputs(dict):
        reset_called = False

        def get(self, key, default=None):
            if not self.reset_called:
                self.reset_called = True
                evaluator.reset()
            return super().get(key, default)

    inputs = ReentrantInputs(_inputs(http_samples=100, http_5xx=5))

    def run() -> None:
        try:
            completed.append(evaluator.evaluate(inputs))
        except BaseException as exc:  # pragma: no cover - assertion relay
            failures.append(exc)

    worker = threading.Thread(target=run, daemon=True)
    worker.start()
    worker.join(timeout=2)

    assert not worker.is_alive(), "input Mapping callback ran under evaluator state lock"
    assert inputs.reset_called is True
    assert not failures
    assert completed[0]["rules"]["http_5xx_ratio"]["transition"] == "triggered"


def test_custom_integer_counts_never_execute_under_the_state_lock():
    evaluator = LocalAlertEvaluator()
    completed: list[dict] = []
    failures: list[BaseException] = []

    class ReentrantCount(int):
        def __lt__(self, other):
            evaluator.reset()
            return super().__lt__(other)

    inputs = _inputs(http_samples=100, http_5xx=5)
    inputs["http"]["sample_size"] = ReentrantCount(100)

    def run() -> None:
        try:
            completed.append(evaluator.evaluate(inputs))
        except BaseException as exc:  # pragma: no cover - assertion relay
            failures.append(exc)

    worker = threading.Thread(target=run, daemon=True)
    worker.start()
    worker.join(timeout=2)

    assert not worker.is_alive(), "custom integer ran under evaluator state lock"
    assert not failures
    rule = completed[0]["rules"]["http_5xx_ratio"]
    assert rule["state"] == "insufficient_data"
    assert rule["reason_code"] == "invalid_aggregate"


def test_silence_datetime_callbacks_are_normalized_before_the_state_lock():
    evaluator = LocalAlertEvaluator()
    completed: list[dict] = []
    failures: list[BaseException] = []

    class ReentrantDateTime(datetime):
        def astimezone(self, tz=None):
            evaluator.reset()
            return super().astimezone(tz)

    now = datetime(2026, 8, 29, tzinfo=timezone.utc)
    expires_at = ReentrantDateTime(2026, 8, 29, 0, 1, tzinfo=timezone.utc)
    silence = AlertSilence(
        "http_5xx_ratio",
        "maintenance",
        now,
        expires_at,
    )

    def run() -> None:
        try:
            completed.append(
                evaluator.evaluate(
                    _inputs(http_samples=100, http_5xx=5),
                    silences=(silence,),
                    now=now,
                )
            )
        except BaseException as exc:  # pragma: no cover - assertion relay
            failures.append(exc)

    worker = threading.Thread(target=run, daemon=True)
    worker.start()
    worker.join(timeout=2)

    assert not worker.is_alive(), "datetime callback ran under evaluator state lock"
    assert not failures
    notification = completed[0]["rules"]["http_5xx_ratio"]["notification"]
    assert notification["state"] == "silenced"
    assert notification["until"] == "2026-08-29T00:01:00Z"


def test_delayed_pre_expiry_evaluation_cannot_rearm_an_expired_silence():
    created_at = datetime(2026, 8, 29, tzinfo=timezone.utc)
    silence = AlertSilence(
        "http_5xx_ratio",
        "maintenance",
        created_at,
        created_at + timedelta(minutes=10),
    )
    evaluator = LocalAlertEvaluator()

    silenced = evaluator.evaluate(
        _inputs(http_samples=100, http_5xx=5),
        silences=(silence,),
        now=created_at,
    )["rules"]["http_5xx_ratio"]
    assert silenced["notification"]["state"] == "silenced"

    after_expiry = evaluator.evaluate(
        _inputs(http_samples=101, http_5xx=5),
        silences=(silence,),
        now=created_at + timedelta(minutes=11),
    )["rules"]["http_5xx_ratio"]
    assert after_expiry["notification"]["state"] == "notify"

    delayed = evaluator.evaluate(
        _inputs(http_samples=101, http_5xx=5),
        silences=(silence,),
        now=created_at + timedelta(minutes=5),
    )["rules"]["http_5xx_ratio"]
    assert delayed["notification"]["state"] == "inactive"

    next_fresh = evaluator.evaluate(
        _inputs(http_samples=102, http_5xx=5),
        silences=(silence,),
        now=created_at + timedelta(minutes=12),
    )["rules"]["http_5xx_ratio"]
    assert next_fresh["state"] == "firing"
    assert next_fresh["notification"]["state"] == "inactive"


def test_canonical_process_evaluator_preserves_deduplication(monkeypatch):
    inputs = _inputs(http_samples=100, http_5xx=5)
    monkeypatch.setattr(
        local_alerts_module,
        "collect_local_alert_inputs",
        lambda: inputs,
    )
    local_alert_evaluator.reset()
    try:
        first = evaluate_local_alerts()["rules"]["http_5xx_ratio"]
        duplicate = evaluate_local_alerts()["rules"]["http_5xx_ratio"]
    finally:
        local_alert_evaluator.reset()

    assert first["transition"] == "triggered"
    assert first["notification"]["state"] == "notify"
    assert duplicate["transition"] == "none"
    assert duplicate["notification"]["state"] == "inactive"


def test_local_alert_evaluation_is_not_added_to_the_public_metrics_endpoint():
    public_metrics = asyncio.run(health_module.metrics())

    assert "local_alerts" not in public_metrics
    assert "alert_inputs" not in public_metrics
    assert all(route.path != "/health/alerts" for route in health_module.router.routes)
