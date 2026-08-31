"""Export OpenMetrics déterministe des agrégats FILON.

Le module ne collecte rien lui-même : il transforme uniquement les snapshots
bornés des registres en mémoire. Les valeurs invalides font échouer l'export au
lieu de produire une série trompeuse ou non parseable.
"""

from __future__ import annotations

import math
from collections.abc import Mapping
from typing import Any


OPENMETRICS_CONTENT_TYPE = (
    "application/openmetrics-text; version=1.0.0; charset=utf-8"
)


class MetricsExportError(ValueError):
    """Le snapshot ne respecte pas le contrat exportable."""


def _mapping(value: object, path: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise MetricsExportError(f"invalid_mapping:{path}")
    return value


def _number(value: object, path: str) -> int | float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise MetricsExportError(f"invalid_number:{path}")
    number = float(value)
    if not math.isfinite(number) or number < 0:
        raise MetricsExportError(f"invalid_number:{path}")
    return value


def _render_number(value: object, path: str) -> str:
    number = _number(value, path)
    if isinstance(number, int):
        return str(number)
    if number.is_integer():
        return str(int(number))
    return format(number, ".15g")


def _escape_label(value: object) -> str:
    label = str(value)
    if any(ord(character) < 32 and character != "\n" for character in label):
        raise MetricsExportError("invalid_label_control_character")
    return label.replace("\\", "\\\\").replace("\n", "\\n").replace('"', '\\"')


def _family(lines: list[str], name: str, description: str, kind: str) -> None:
    lines.append(f"# HELP {name} {description}")
    lines.append(f"# TYPE {name} {kind}")


def _sample(
    lines: list[str],
    name: str,
    value: object,
    *,
    path: str,
    labels: Mapping[str, object] | None = None,
) -> None:
    suffix = ""
    if labels:
        rendered = ",".join(
            f'{key}="{_escape_label(label)}"'
            for key, label in sorted(labels.items())
        )
        suffix = "{" + rendered + "}"
    lines.append(f"{name}{suffix} {_render_number(value, path)}")


def _counter_map(
    lines: list[str],
    *,
    family: str,
    description: str,
    values: object,
    label_name: str,
    path: str,
) -> None:
    _family(lines, family, description, "counter")
    for label, count in sorted(_mapping(values, path).items()):
        _sample(
            lines,
            family,
            count,
            path=f"{path}.{label}",
            labels={label_name: label},
        )


def _latency_samples(
    lines: list[str],
    *,
    family: str,
    description: str,
    latency: object,
    path: str,
    labels: Mapping[str, object] | None = None,
    declare: bool = True,
) -> None:
    values = _mapping(latency, path)
    if declare:
        _family(lines, family, description, "gauge")
    for statistic in ("average", "p50", "p95", "p99", "maximum"):
        value = values.get(statistic)
        if value is None:
            continue
        merged_labels = dict(labels or {})
        merged_labels["statistic"] = statistic
        _sample(
            lines,
            family,
            float(_number(value, f"{path}.{statistic}")) / 1000,
            path=f"{path}.{statistic}",
            labels=merged_labels,
        )


def _route_parts(route_key: object) -> tuple[str, str]:
    key = str(route_key)
    if key == "OTHER":
        return "OTHER", "OTHER"
    method, separator, route = key.partition(" ")
    if not separator or not method or not route:
        raise MetricsExportError("invalid_route_key")
    return method, route


def render_openmetrics(
    request_snapshot: Mapping[str, Any],
    product_snapshot: Mapping[str, Any],
) -> str:
    """Rend les deux snapshots sous forme OpenMetrics 1.0.

    Aucun payload, identifiant, requête, titre produit ou valeur marchande
    n'est accepté comme dimension. Les seules valeurs variables sont les
    templates de routes FastAPI déjà bornés par le registre HTTP.
    """

    lines: list[str] = []

    _family(
        lines,
        "filon_process_uptime_seconds",
        "Durée de vie du processus FILON observé.",
        "gauge",
    )
    _sample(
        lines,
        "filon_process_uptime_seconds",
        request_snapshot.get("uptime_seconds"),
        path="request.uptime_seconds",
    )

    overall = _mapping(request_snapshot.get("overall"), "request.overall")
    _family(
        lines,
        "filon_http_requests_total",
        "Nombre total de requêtes HTTP observées par ce processus.",
        "counter",
    )
    _sample(
        lines,
        "filon_http_requests_total",
        overall.get("requests"),
        path="request.overall.requests",
    )
    _counter_map(
        lines,
        family="filon_http_responses_total",
        description="Réponses HTTP par famille de statut bornée.",
        values=overall.get("status_groups"),
        label_name="status_group",
        path="request.overall.status_groups",
    )
    _latency_samples(
        lines,
        family="filon_http_latency_seconds",
        description="Latence HTTP locale en secondes, statistiques bornées.",
        latency=overall.get("latency_ms"),
        path="request.overall.latency_ms",
    )

    routes = _mapping(request_snapshot.get("routes"), "request.routes")
    _family(
        lines,
        "filon_http_route_requests_total",
        "Requêtes HTTP par méthode et template de route bornés.",
        "counter",
    )
    _family(
        lines,
        "filon_http_route_responses_total",
        "Réponses HTTP par méthode, template de route et famille de statut.",
        "counter",
    )
    _family(
        lines,
        "filon_http_route_latency_seconds",
        "Latence locale par template de route en secondes.",
        "gauge",
    )
    for route_key, raw_series in sorted(routes.items()):
        method, route = _route_parts(route_key)
        labels = {"method": method, "route": route}
        series = _mapping(raw_series, f"request.routes.{route_key}")
        _sample(
            lines,
            "filon_http_route_requests_total",
            series.get("requests"),
            path=f"request.routes.{route_key}.requests",
            labels=labels,
        )
        for status_group, count in sorted(
            _mapping(
                series.get("status_groups"),
                f"request.routes.{route_key}.status_groups",
            ).items()
        ):
            _sample(
                lines,
                "filon_http_route_responses_total",
                count,
                path=f"request.routes.{route_key}.status_groups.{status_group}",
                labels={**labels, "status_group": status_group},
            )
        _latency_samples(
            lines,
            family="filon_http_route_latency_seconds",
            description="Latence locale par template de route en secondes.",
            latency=series.get("latency_ms"),
            path=f"request.routes.{route_key}.latency_ms",
            labels=labels,
            declare=False,
        )

    if product_snapshot.get("schema_version") != 1:
        raise MetricsExportError("unsupported_product_metrics_schema")
    decisions = _mapping(
        product_snapshot.get("decision_evaluations"),
        "product.decision_evaluations",
    )
    _family(
        lines,
        "filon_decision_evaluations_total",
        "Évaluations de décision Product Intelligence.",
        "counter",
    )
    _sample(
        lines,
        "filon_decision_evaluations_total",
        decisions.get("total"),
        path="product.decision_evaluations.total",
    )
    for key, family, label, description in (
        ("scopes", "filon_decision_scope_total", "scope", "Décisions par périmètre borné."),
        ("confidence", "filon_decision_confidence_total", "confidence", "Décisions par niveau documentaire borné."),
        ("offer_kinds", "filon_decision_offer_kind_total", "offer_kind", "Décisions par nature d'offre bornée."),
        ("freshness_status", "filon_decision_freshness_status_total", "status", "Décisions par état de fraîcheur borné."),
        ("freshness_age_buckets", "filon_decision_freshness_age_total", "bucket", "Décisions par tranche d'âge bornée."),
        ("missing_dimensions", "filon_decision_missing_dimension_total", "dimension", "Dimensions explicitement inconnues."),
        ("evidence_states", "filon_decision_evidence_state_total", "state", "États de preuve bornés."),
        ("exclusions", "filon_decision_exclusion_total", "reason", "Exclusions de décision par motif borné."),
    ):
        _counter_map(
            lines,
            family=family,
            description=description,
            values=decisions.get(key),
            label_name=label,
            path=f"product.decision_evaluations.{key}",
        )

    recommendations = _mapping(
        product_snapshot.get("recommendation_responses"),
        "product.recommendation_responses",
    )
    _family(
        lines,
        "filon_recommendation_responses_total",
        "Réponses de recommandation remises par FILON.",
        "counter",
    )
    _sample(
        lines,
        "filon_recommendation_responses_total",
        recommendations.get("total"),
        path="product.recommendation_responses.total",
    )
    for key, family, label, description in (
        ("outcomes", "filon_recommendation_outcome_total", "outcome", "Réponses documentées ou abstentions."),
        ("delivery", "filon_recommendation_delivery_total", "delivery", "Réponses par mode de livraison borné."),
        ("card_count_buckets", "filon_recommendation_card_count_total", "bucket", "Réponses par nombre borné de cartes."),
    ):
        _counter_map(
            lines,
            family=family,
            description=description,
            values=recommendations.get(key),
            label_name=label,
            path=f"product.recommendation_responses.{key}",
        )
    _family(
        lines,
        "filon_recommendation_buy_cards_total",
        "Cartes dont l'action buy a été autorisée par le moteur déterministe.",
        "counter",
    )
    _sample(
        lines,
        "filon_recommendation_buy_cards_total",
        recommendations.get("buy_cards"),
        path="product.recommendation_responses.buy_cards",
    )

    stages = _mapping(product_snapshot.get("pipeline_stages"), "product.pipeline_stages")
    _family(
        lines,
        "filon_pipeline_executions_total",
        "Exécutions des étapes Product Intelligence par étape bornée.",
        "counter",
    )
    _family(
        lines,
        "filon_pipeline_outcomes_total",
        "Sorties des étapes Product Intelligence par état borné.",
        "counter",
    )
    _family(
        lines,
        "filon_pipeline_latency_seconds",
        "Latence locale des étapes Product Intelligence en secondes.",
        "gauge",
    )
    for stage, raw_series in sorted(stages.items()):
        series = _mapping(raw_series, f"product.pipeline_stages.{stage}")
        _sample(
            lines,
            "filon_pipeline_executions_total",
            series.get("executions"),
            path=f"product.pipeline_stages.{stage}.executions",
            labels={"stage": stage},
        )
        for outcome, count in sorted(
            _mapping(
                series.get("outcomes"),
                f"product.pipeline_stages.{stage}.outcomes",
            ).items()
        ):
            _sample(
                lines,
                "filon_pipeline_outcomes_total",
                count,
                path=f"product.pipeline_stages.{stage}.outcomes.{outcome}",
                labels={"outcome": outcome, "stage": stage},
            )
        _latency_samples(
            lines,
            family="filon_pipeline_latency_seconds",
            description="Latence locale des étapes Product Intelligence en secondes.",
            latency=series.get("latency_ms"),
            path=f"product.pipeline_stages.{stage}.latency_ms",
            labels={"stage": stage},
            declare=False,
        )

    lines.append("# EOF")
    return "\n".join(lines) + "\n"
