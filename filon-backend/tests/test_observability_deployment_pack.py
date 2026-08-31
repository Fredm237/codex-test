from __future__ import annotations

import json
import re
from collections.abc import Iterable
from pathlib import Path
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[1]
PACK = ROOT / "observability"
PROMETHEUS_CONFIG = PACK / "prometheus" / "prometheus.yml"
PROMETHEUS_RULES = PACK / "prometheus" / "rules" / "filon.rules.yml"
PROMETHEUS_RULE_TESTS = (
    PACK / "prometheus" / "rules" / "filon.rules.test.yml"
)
PROMETHEUS_TARGETS = PACK / "prometheus" / "targets" / "filon.json"
PROMETHEUS_TARGET_SCHEMA = (
    PACK / "schemas" / "prometheus-target-inventory.schema.json"
)
PROMETHEUS_RECEIPT_SCHEMA = (
    PACK / "schemas" / "prometheus-activation-receipt.schema.json"
)
GRAFANA_DASHBOARD = PACK / "grafana" / "filon-core-observability.json"
EXPORTER = ROOT / "app" / "core" / "metrics_export.py"

EXPECTED_RECORDS = {
    "filon:http_request_rate5m",
    "filon:http_5xx_ratio5m",
    "filon:recommendation_rate5m",
    "filon:recommendation_abstention_ratio5m",
    "filon:assistant_timeout_ratio5m",
    "filon:pipeline_execution_rate5m",
    "filon:pipeline_error_ratio5m",
    "filon:decision_rate5m",
    "filon:buy_card_rate5m",
    "filon:missing_dimension_rate5m",
    "filon:decision_exclusion_rate5m",
}


def _yaml(path: Path) -> dict[str, Any]:
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def _strings(value: Any) -> Iterable[str]:
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for key, nested in value.items():
            yield str(key)
            yield from _strings(nested)
    elif isinstance(value, list):
        for nested in value:
            yield from _strings(nested)


def _contains_key(value: Any, forbidden: str) -> bool:
    if isinstance(value, dict):
        return forbidden in value or any(
            _contains_key(nested, forbidden) for nested in value.values()
        )
    if isinstance(value, list):
        return any(_contains_key(nested, forbidden) for nested in value)
    return False


def _exported_metric_names() -> set[str]:
    source = EXPORTER.read_text(encoding="utf-8")
    return set(re.findall(r'"(filon_[a-z0-9_]+)"', source))


def _dashboard() -> dict[str, Any]:
    value = json.loads(GRAFANA_DASHBOARD.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def _panel_targets(dashboard: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        target
        for panel in dashboard["panels"]
        for target in panel.get("targets", [])
    ]


def test_prometheus_scrape_is_bounded_secret_file_only_and_empty_by_default():
    config = _yaml(PROMETHEUS_CONFIG)
    assert config["global"] == {
        "scrape_interval": "30s",
        "scrape_timeout": "10s",
        "evaluation_interval": "30s",
    }
    assert config["rule_files"] == ["/etc/prometheus/rules/filon.rules.yml"]
    assert len(config["scrape_configs"]) == 1
    scrape = config["scrape_configs"][0]
    assert scrape["job_name"] == "filon-backend"
    assert scrape["scheme"] == "https"
    assert scrape["metrics_path"] == "/health/metrics/openmetrics"
    assert scrape["honor_labels"] is False
    assert scrape["authorization"] == {
        "type": "Bearer",
        "credentials_file": "/run/secrets/filon_metrics_export_token",
    }
    assert "credentials" not in scrape["authorization"]
    assert "params" not in scrape
    assert "static_configs" not in scrape
    assert "basic_auth" not in scrape
    assert scrape["file_sd_configs"] == [
        {
            "files": ["/etc/prometheus/targets/filon.json"],
            "refresh_interval": "30s",
        }
    ]
    assert scrape["relabel_configs"] == [
        {
            "source_labels": ["environment", "cluster", "replica"],
            "separator": ";",
            "regex": ".+;.+;.+",
            "action": "keep",
        }
    ]
    assert scrape["metric_relabel_configs"] == [
        {
            "action": "labelkeep",
            "regex": (
                "__name__|job|instance|environment|cluster|replica|"
                "status_group|statistic|method|route|scope|confidence|"
                "offer_kind|status|bucket|dimension|state|reason|outcome|"
                "delivery|stage"
            ),
        }
    ]
    assert scrape["sample_limit"] == 2500
    assert scrape["target_limit"] == 100
    assert scrape["label_limit"] == 10
    assert scrape["label_name_length_limit"] == 64
    assert scrape["label_value_length_limit"] == 256
    assert scrape["body_size_limit"] == "1MB"
    assert json.loads(PROMETHEUS_TARGETS.read_text(encoding="utf-8")) == []


def test_recording_rules_use_only_exported_counters_and_keep_latency_local():
    rules = _yaml(PROMETHEUS_RULES)
    assert len(rules["groups"]) == 1
    group = rules["groups"][0]
    assert group["name"] == "filon-rollups-v1"
    assert group["interval"] == "30s"
    assert group["limit"] == 100
    entries = group["rules"]
    assert {entry["record"] for entry in entries} == EXPECTED_RECORDS
    assert all("alert" not in entry for entry in entries)

    exported = _exported_metric_names()
    ratio_records = {
        "filon:http_5xx_ratio5m",
        "filon:recommendation_abstention_ratio5m",
        "filon:assistant_timeout_ratio5m",
        "filon:pipeline_error_ratio5m",
    }
    for entry in entries:
        expression = entry["expr"]
        metric_names = set(re.findall(r"\bfilon_[a-z0-9_]+\b", expression))
        assert metric_names
        assert metric_names <= exported
        assert '{job="filon-backend"}' in expression or 'job="filon-backend",' in expression
        assert "[5m]" in expression
        assert "latency" not in expression
        if entry["record"] in ratio_records:
            assert "clamp_min(" in expression
            assert "1e-9" in expression
        else:
            assert "clamp_min(" not in expression

    by_record = {entry["record"]: entry["expr"] for entry in entries}
    assert "sum by (environment, cluster, stage)" in by_record[
        "filon:pipeline_error_ratio5m"
    ]
    assert "sum by (environment, cluster, dimension)" in by_record[
        "filon:missing_dimension_rate5m"
    ]
    assert "sum by (environment, cluster, reason)" in by_record[
        "filon:decision_exclusion_rate5m"
    ]


def test_grafana_dashboard_is_descriptive_secret_free_and_metric_closed():
    dashboard = _dashboard()
    assert dashboard["schemaVersion"] == 42
    assert dashboard["uid"] == "filon-core-observability-v1"
    assert dashboard["timezone"] == "utc"
    assert dashboard["refresh"] == "30s"
    assert dashboard["tags"] == ["filon", "product-intelligence", "no-slo"]
    assert "ni des SLO ni des preuves de santé" in dashboard["description"]
    assert dashboard["annotations"] == {"list": []}
    assert not _contains_key(dashboard, "alert")
    assert not _contains_key(dashboard, "thresholds")

    lowered = "\n".join(_strings(dashboard)).lower()
    for forbidden in (
        "authorization: bearer",
        "metrics_export_token",
        "/run/secrets/",
        "password",
        "api_key",
    ):
        assert forbidden not in lowered

    targets = _panel_targets(dashboard)
    assert len(targets) == len(dashboard["panels"])
    expressions = [target["expr"] for target in targets]
    assert all('environment=~"$environment"' in expr for expr in expressions)
    assert all('cluster=~"$cluster"' in expr for expr in expressions)

    exported = _exported_metric_names()
    raw_names = set(
        re.findall(r"\bfilon_[a-z][a-z0-9_]*\b", "\n".join(expressions))
    )
    recorded_names = set(
        re.findall(r"\bfilon:[a-z][a-z0-9_]*\b", "\n".join(expressions))
    )
    assert raw_names <= exported
    assert recorded_names <= EXPECTED_RECORDS

    panels = {panel["id"]: panel for panel in dashboard["panels"]}
    assert set(panels) == set(range(1, 17))
    for panel_id in (9, 10):
        target = panels[panel_id]["targets"][0]
        assert "sum" not in target["expr"]
        assert 'instance=~"$instance"' in target["expr"]
        assert "{{instance}}" in target["legendFormat"]
        assert "local" in panels[panel_id]["description"].lower()


def test_dashboard_grid_does_not_overlap_and_variables_are_closed():
    dashboard = _dashboard()
    panels = dashboard["panels"]
    for index, left in enumerate(panels):
        left_grid = left["gridPos"]
        assert 0 <= left_grid["x"] < 24
        assert 1 <= left_grid["w"] <= 24
        assert left_grid["x"] + left_grid["w"] <= 24
        assert left_grid["h"] > 0
        for right in panels[index + 1 :]:
            right_grid = right["gridPos"]
            horizontal_overlap = (
                left_grid["x"] < right_grid["x"] + right_grid["w"]
                and right_grid["x"] < left_grid["x"] + left_grid["w"]
            )
            vertical_overlap = (
                left_grid["y"] < right_grid["y"] + right_grid["h"]
                and right_grid["y"] < left_grid["y"] + left_grid["h"]
            )
            assert not (horizontal_overlap and vertical_overlap)

    variables = dashboard["templating"]["list"]
    assert [variable["name"] for variable in variables] == [
        "environment",
        "cluster",
        "instance",
    ]
    for variable in variables:
        assert variable["type"] == "query"
        assert variable["includeAll"] is True
        assert variable["multi"] is True
        assert variable["allValue"] == ".*"
        assert variable["datasource"] == {
            "type": "prometheus",
            "uid": "${DS_PROMETHEUS}",
        }


def test_pack_documents_external_activation_without_shipping_fake_targets():
    readme = (PACK / "README.md").read_text(encoding="utf-8")
    assert "Prometheus **3.13.2 LTS**" in readme
    assert "promtool check config" in readme
    assert "promtool check rules" in readme
    assert "promtool test rules" in readme
    assert "load balancer" in readme
    assert "replica-a.internal.example:443" in readme
    assert "observability.tools.target_inventory" in readme
    assert "observability.tools.verify_prometheus" in readme
    assert "--expected-replicas" in readme
    assert "--allow-empty" in readme
    assert "fingerprint" in readme
    assert "ni SLO" in readme
    assert "pager" in readme
    assert json.loads(PROMETHEUS_TARGETS.read_text(encoding="utf-8")) == []

    rule_tests = _yaml(PROMETHEUS_RULE_TESTS)
    assert rule_tests["rule_files"] == ["filon.rules.yml"]
    assert rule_tests["evaluation_interval"] == "1m"
    assert len(rule_tests["tests"]) == 1
    expressions = rule_tests["tests"][0]["promql_expr_test"]
    assert len(expressions) == len(EXPECTED_RECORDS)

    target_schema = json.loads(
        PROMETHEUS_TARGET_SCHEMA.read_text(encoding="utf-8")
    )
    assert target_schema["type"] == "array"
    assert target_schema["maxItems"] == 100
    group_schema = target_schema["items"]
    assert group_schema["additionalProperties"] is False
    assert group_schema["properties"]["targets"]["maxItems"] == 1
    assert (
        group_schema["properties"]["labels"]["additionalProperties"] is False
    )

    receipt_schema = json.loads(
        PROMETHEUS_RECEIPT_SCHEMA.read_text(encoding="utf-8")
    )
    assert receipt_schema["additionalProperties"] is False
    assert receipt_schema["properties"]["prometheus_version"]["const"] == "3.13.2"
    assert (
        set(receipt_schema["$defs"]["ruleRoster"]["items"]["enum"])
        == EXPECTED_RECORDS
    )
