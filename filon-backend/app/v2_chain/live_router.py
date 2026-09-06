"""Routage atomique Core V1 / V2 pour les surfaces d'achat publiques.

Le routeur calcule toujours Core avant toute tentative V2. Une autorisation
persistée, une cohorte, une preuve de fraîcheur ou une écriture de télémétrie
manquante conserve donc la réponse Core entière. Aucun champ des deux moteurs
n'est fusionné et aucun texte de requête n'est persisté.
"""

from __future__ import annotations

import secrets
from collections.abc import Mapping
from dataclasses import dataclass, replace
from datetime import datetime, timezone
from typing import Any, Literal

from app.core.config import get_settings
from app.core.logging import get_logger
from app.db import session as db
from app.v2_chain.canary import (
    CanaryAssignment,
    V2CanaryEligibilityEvidence,
    V2CanaryEligibilityPolicy,
    V2CanaryPayload,
    assign_closed_cohort,
    evaluate_canary_eligibility,
    run_canary_read,
)
from app.v2_chain.canary_observation import record_canary_read
from app.v2_chain.live_dark_reader import infer_supported_vertical
from app.v2_chain.online_reader import (
    V2OnlineReadRequest,
    inspect_v2_online,
    read_v2_online,
)
from app.v2_chain.promotion_guard import (
    V2RuntimeAuthorization,
    authorize_v2_runtime,
    load_authorized_canary_gate,
)
from app.v2_chain.qualification import RESPONSE_TYPES
from quality_lab.v2_canary import V2CanaryGateReport


log = get_logger("v2_live_router")
Surface = Literal["advise", "advise_stream"]


@dataclass(frozen=True)
class V2LiveRouteResult:
    response: Mapping[str, Any]
    source: str
    mode: str
    reason_code: str


def _language(locale: str | None) -> str:
    value = (locale or "fr").strip().lower().split("-")[0]
    return value if value in {"fr", "nl", "en"} else "fr"


def _country(value: str | None, locale: str | None) -> str | None:
    candidate = (value or "").strip().split("-")[0].upper()
    if len(candidate) == 2 and candidate.isalpha():
        return candidate
    parts = (locale or "").strip().split("-")
    if len(parts) > 1:
        candidate = parts[-1].upper()
        if len(candidate) == 2 and candidate.isalpha():
            return candidate
    return None


def _eligibility_locale(locale: str | None) -> str:
    value = (locale or "fr").strip()
    return value[:8] if value else "fr"


def _runtime_gate(authorization: V2RuntimeAuthorization) -> V2CanaryGateReport:
    blocked = tuple(
        sorted(RESPONSE_TYPES - set(authorization.authorized_response_types))
    )
    return V2CanaryGateReport(
        schema_version="v2-shadow-to-canary-gate/v1",
        status="CANARY_AUTHORIZED",
        gates={},
        blocked_response_types=blocked,
        blocker_codes=tuple(f"RESPONSE_TYPE_OFF:{value}" for value in blocked),
        evaluation_id=authorization.gate_evaluation_id,
    )


def _public_abstention(
    *,
    surface: Surface,
    query: str,
    vertical: str,
    country: str | None,
) -> dict[str, Any]:
    if surface == "advise_stream":
        return {
            "usage": query,
            "offers": 0,
            "cards": [],
            "real": False,
            "currency": None,
            "country": (country or "be").lower(),
        }
    return {
        "query": query,
        "criteria": {
            "category": vertical,
            "budget_max": None,
            "usage": [],
            "must_have": [],
            "priorities": [],
            "keywords": [],
        },
        "recommendation": None,
        "alternatives": [],
        "trace": [],
    }


def _core_accepts_abstention(
    *,
    surface: Surface,
    response: Mapping[str, Any],
) -> bool:
    """Autorise ABSTAIN uniquement si Core ne possède aucun résultat réel.

    La première version du lecteur V2 ne sait servir qu'une abstention. Elle ne
    doit donc jamais retirer une recommandation ou une carte réelle déjà
    disponible dans Core V1. Toute forme inattendue conserve Core.
    """

    if surface == "advise_stream":
        return (
            response.get("real") is False
            and response.get("offers") == 0
            and response.get("cards") == []
        )
    return (
        response.get("recommendation") is None
        and response.get("alternatives") == []
    )


async def route_promoted_response(
    *,
    core_response: Mapping[str, Any],
    core_latency_us: int,
    query: str,
    budget: float | None,
    country: str | None,
    locale: str | None,
    surface: Surface,
    subject_digest: str | None,
) -> V2LiveRouteResult:
    """Remplace Core seulement par un bloc V2 entièrement autorisé."""

    try:
        settings = get_settings()
    except Exception as exc:
        log.warning("V2 live configuration held (error_type=%s)", type(exc).__name__)
        return V2LiveRouteResult(
            core_response, "core_v1", "unknown", "configuration_hold"
        )
    mode = settings.v2_chain_mode
    if mode not in {"canary", "public"}:
        return V2LiveRouteResult(core_response, "core_v1", mode, "reader_off")
    if surface not in {"advise", "advise_stream"}:
        raise ValueError("V2 live surface is unsupported")
    if not isinstance(core_response, Mapping):
        raise ValueError("Core response is invalid")

    vertical = infer_supported_vertical(query)
    if vertical is None:
        return V2LiveRouteResult(
            core_response, "core_v1", mode, "vertical_unsupported"
        )

    assignment = (
        assign_closed_cohort(
            subject_digest=subject_digest,
            allowed_subject_digests=settings.v2_canary_subject_digests_list,
        )
        if mode == "canary"
        else CanaryAssignment("canary", "public_authorized")
    )
    # Hors cohorte, CANARY ne doit ajouter ni accès base ni latence à Core.
    if assignment.cohort != "canary":
        return V2LiveRouteResult(
            core_response, "core_v1", mode, assignment.reason_code
        )

    evaluated_at = datetime.now(timezone.utc)
    try:
        async with db.session_scope() as session:
            if session is None:
                return V2LiveRouteResult(
                    core_response, "core_v1", mode, "database_unavailable"
                )
            authorization = await authorize_v2_runtime(session, settings=settings)
            gate = (
                await load_authorized_canary_gate(
                    session,
                    receipt_evaluation_id=authorization.receipt_evaluation_id,
                )
                if mode == "canary"
                else _runtime_gate(authorization)
            )
            online_request = V2OnlineReadRequest(
                query=query,
                vertical=vertical,
                locale=_language(locale),
                country_code=_country(country, locale),
                budget_amount_decimal=(
                    f"{budget:.2f}" if budget is not None else None
                ),
                budget_currency="EUR" if budget is not None else None,
            )
            inspection = await inspect_v2_online(
                session,
                online_request,
                evaluated_at=evaluated_at,
            )
            eligibility = evaluate_canary_eligibility(
                policy=V2CanaryEligibilityPolicy(
                    policy_id=authorization.gate_evaluation_id,
                    supported_verticals=tuple(settings.v2_supported_verticals_list),
                    supported_locales=tuple(settings.v2_supported_locales_list),
                    supported_decision_types=tuple(
                        settings.v2_supported_decision_types_list
                    ),
                    maximum_data_age_seconds=settings.v2_max_data_age_seconds,
                ),
                evidence=V2CanaryEligibilityEvidence(
                    vertical=vertical,
                    locale=_eligibility_locale(locale),
                    decision_type="purchase_advice",
                    data_age_seconds=inspection.data_age_seconds,
                    dependencies_admissible=inspection.dependencies_admissible,
                    # Le lecteur actuellement qualifié ne sert qu'ABSTAIN : il
                    # ne formule donc aucun claim affecté par un fait inconnu.
                    # Le lecteur qualifié ne produit encore qu'ABSTAIN. Une
                    # réponse Core réelle interdit donc son remplacement.
                    critical_unknown=not _core_accepts_abstention(
                        surface=surface,
                        response=core_response,
                    ),
                    hard_constraint_violation=False,
                    confidence_required=False,
                    confidence_admissible=False,
                    rollback_available=True,
                ),
            )

            async def core_reader() -> Mapping[str, Any]:
                return core_response

            async def v2_reader() -> V2CanaryPayload:
                payload = await read_v2_online(
                    session,
                    online_request,
                    evaluated_at=evaluated_at,
                    inspection=inspection,
                )
                if payload.response_type != "ABSTAIN":
                    raise RuntimeError("public response adapter is not qualified")
                return replace(
                    payload,
                    response=_public_abstention(
                        surface=surface,
                        query=query,
                        vertical=vertical,
                        country=country,
                    ),
                )

            routed = await run_canary_read(
                assignment=assignment,
                eligibility=eligibility,
                gate=gate,
                core_reader=core_reader,
                v2_reader=v2_reader,
            )
            measured_core = max(0, int(core_latency_us))
            receipt = replace(
                routed.receipt,
                core_latency_us=measured_core,
                total_latency_us=measured_core + (routed.receipt.v2_latency_us or 0),
            )
            # La preuve agrégée reste obligatoire après la promotion. Les
            # lignes PUBLIC portent le gate public exact et la raison
            # ``public_authorized`` ; elles ne gonflent donc jamais le gate
            # CANARY source.
            if assignment.cohort == "canary":
                await record_canary_read(
                    session,
                    observation_key=secrets.token_hex(32),
                    receipt=receipt,
                    evaluated_at=evaluated_at,
                    apply=True,
                )
                await session.commit()
            return V2LiveRouteResult(
                routed.response,
                routed.receipt.source,
                mode,
                routed.receipt.fallback_reason or "v2_authorized",
            )
    except Exception as exc:
        # Ni contenu de requête, ni détail fournisseur dans le journal.
        log.warning("V2 live routing held (error_type=%s)", type(exc).__name__)
        return V2LiveRouteResult(core_response, "core_v1", mode, "runtime_hold")
