"""Dual-read V1/V2 sur trafic réel, sans influence publique ni texte persistant."""

from __future__ import annotations

import secrets
import time
from collections.abc import Mapping
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any

from app.core.config import get_settings
from app.core.logging import get_logger
from app.db import session as db
from app.v2_chain.models import V2LiveDarkReadObservation
from app.v2_chain.online_reader import V2OnlineReadRequest, read_v2_online


log = get_logger("v2_live_dark_reader")
COMPARISON_VERSION = "v2-live-dark-reader/v1"
SUPPORTED_LOCALES = {"fr", "nl", "en"}
VERTICAL_TERMS: dict[str, tuple[str, ...]] = {
    "smartphones": (
        "smartphone",
        "téléphone",
        "telephone",
        "iphone",
        "galaxy",
        "gsm",
        "phone",
    ),
    "laptops": (
        "ordinateur portable",
        "pc portable",
        "laptop",
        "notebook",
        "macbook",
    ),
    "audio": (
        "casque",
        "écouteur",
        "ecouteur",
        "earbud",
        "headphone",
        "enceinte",
        "speaker",
    ),
    "fashion": (
        "robe",
        "veste",
        "chaussure",
        "sneaker",
        "chemise",
        "pantalon",
        "mode",
    ),
    "appliances_hvac": (
        "climatiseur",
        "chauffage",
        "aspirateur",
        "réfrigérateur",
        "refrigerateur",
        "lave-linge",
        "air conditioner",
    ),
    "tyres": ("pneu", "pneus", "tyre", "tyres", "tire", "tires"),
}


@dataclass(frozen=True)
class CoreReadSummary:
    outcome: str
    candidate_count: int


@dataclass(frozen=True)
class LiveDarkReadReport:
    schema_version: str
    status: str
    observation_key: str | None
    vertical: str | None
    core_outcome: str | None
    v2_outcome: str | None
    classification: str | None
    raw_query_retained: bool = False


def _elapsed_us(started_ns: int) -> int:
    return max(0, (time.perf_counter_ns() - started_ns) // 1_000)


def _locale(value: str | None) -> str:
    locale = (value or "fr").strip().lower().split("-")[0]
    return locale if locale in SUPPORTED_LOCALES else "fr"


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


def infer_supported_vertical(query: str) -> str | None:
    """Classe une verticale seulement sur un marqueur explicite et non ambigu."""

    normalized = " ".join(query.casefold().split())
    matches = [
        vertical
        for vertical, terms in VERTICAL_TERMS.items()
        if any(term in normalized for term in terms)
    ]
    return matches[0] if len(matches) == 1 else None


def summarize_core_response(response: Mapping[str, Any]) -> CoreReadSummary:
    """Réduit la réponse V1 aux seuls compteurs nécessaires à la comparaison."""

    cards = response.get("cards")
    if isinstance(cards, list):
        count = len([item for item in cards if isinstance(item, Mapping)])
        return CoreReadSummary("CANDIDATES" if count else "NO_MATCH", count)
    recommendation = response.get("recommendation")
    alternatives = response.get("alternatives")
    count = int(isinstance(recommendation, Mapping))
    if isinstance(alternatives, list):
        count += len([item for item in alternatives if isinstance(item, Mapping)])
    return CoreReadSummary("CANDIDATES" if count else "NO_MATCH", count)


def _classification(
    *,
    core: CoreReadSummary,
    v2_outcome: str,
    safety_state: str,
) -> str:
    if v2_outcome == "UNSUPPORTED":
        return "V2_UNSUPPORTED"
    if v2_outcome == "ERROR" or safety_state == "INVALID":
        return "ENGINE_PROBLEM"
    if v2_outcome == "ABSTAIN" and core.outcome == "NO_MATCH":
        return "V2_ABSTAINS_CORRECTLY"
    # Sans vérité humaine indépendante, une divergence factuellement sûre ne
    # devient jamais artificiellement une amélioration de V1 ou de V2.
    if v2_outcome in {"BUY_NOW", "WAIT"} and core.outcome == "CANDIDATES":
        return "BOTH_VALID"
    return "AMBIGUOUS"


async def observe_live_dark_read(
    *,
    query: str,
    budget: float | None,
    country: str | None,
    locale: str | None,
    core_response: Mapping[str, Any],
    core_latency_us: int,
    surface: str,
) -> LiveDarkReadReport:
    """Exécute V2 après la réponse V1 et ne persiste que des agrégats privés."""

    settings = get_settings()
    if settings.v2_chain_mode != "dark":
        return LiveDarkReadReport(
            "v2-live-dark-read-report/v1", "off", None, None, None, None, None
        )
    campaign_id = settings.v2_chain_campaign_id
    if (
        not isinstance(campaign_id, str)
        or not campaign_id.startswith("sha256:")
        or len(campaign_id) != 71
    ):
        raise RuntimeError("live dark reader requires an exact campaign digest")
    if surface not in {"advise", "advise_stream"}:
        raise ValueError("live dark surface is unsupported")
    core = summarize_core_response(core_response)
    language = _locale(locale)
    country_code = _country(country, locale)
    vertical = infer_supported_vertical(query)
    evaluated = datetime.now(timezone.utc)
    v2_started = time.perf_counter_ns()
    v2_outcome = "UNSUPPORTED"
    v2_candidates = 0
    chain_complete = False
    safety_state = "UNSUPPORTED"
    provenance_complete = False

    async with db.session_scope() as session:
        if session is None:
            return LiveDarkReadReport(
                "v2-live-dark-read-report/v1",
                "database_unavailable",
                None,
                vertical,
                core.outcome,
                None,
                None,
            )
        if vertical is not None:
            try:
                payload = await read_v2_online(
                    session,
                    V2OnlineReadRequest(
                        query=query,
                        vertical=vertical,
                        locale=language,
                        country_code=country_code,
                        budget_amount_decimal=(
                            f"{budget:.2f}" if budget is not None else None
                        ),
                        budget_currency="EUR" if budget is not None else None,
                    ),
                    evaluated_at=evaluated,
                )
                v2_outcome = payload.response_type
                items = payload.response.get("items")
                v2_candidates = len(items) if isinstance(items, list) else 0
                chain_complete = payload.chain_complete
                safety_state = payload.safety_state
                provenance_complete = payload.provenance_complete
            except Exception as exc:
                log.warning("V2 live dark read failed (error_type=%s)", type(exc).__name__)
                v2_outcome = "ERROR"
                safety_state = "INVALID"

        classification = _classification(
            core=core,
            v2_outcome=v2_outcome,
            safety_state=safety_state,
        )
        observation_key = secrets.token_hex(32)
        session.add(
            V2LiveDarkReadObservation(
                observation_key=observation_key,
                campaign_id=campaign_id,
                comparison_version=COMPARISON_VERSION,
                surface=surface,
                vertical=vertical,
                locale=language,
                country_code=country_code,
                core_outcome=core.outcome,
                v2_outcome=v2_outcome,
                classification=classification,
                core_candidate_count=core.candidate_count,
                v2_candidate_count=v2_candidates,
                core_latency_us=max(0, int(core_latency_us)),
                v2_latency_us=_elapsed_us(v2_started),
                chain_complete=chain_complete,
                safety_state=safety_state,
                provenance_complete=provenance_complete,
                raw_query_retained=False,
                evaluated_at=evaluated.replace(tzinfo=None),
            )
        )
        await session.commit()

    return LiveDarkReadReport(
        "v2-live-dark-read-report/v1",
        "recorded",
        observation_key,
        vertical,
        core.outcome,
        v2_outcome,
        classification,
    )


def report_dict(report: LiveDarkReadReport) -> dict[str, object]:
    return asdict(report)
