"""Affiliation Awin — génération de liens affiliés et synchronisation des annonceurs.

Principe : dès qu'un programme marchand est validé sur Awin, ce module transforme
automatiquement le lien d'une offre en **lien affilié Awin** (deep-link), pour que
les clics soient rémunérés — sans rien changer d'autre dans FILON.

- `ensure_advertisers()` : récupère (et met en cache) la liste des annonceurs
  auxquels l'éditeur est **inscrit** (API Awin, Bearer token). Sans token ou sans
  programme validé, la liste est vide et l'on retombe proprement sur le lien direct.
- `affiliate_link(url, merchant)` : renvoie le deep-link Awin si le marchand
  correspond à un annonceur inscrit, sinon le lien d'origine (jamais d'erreur).

Le token API est lu depuis la config (variable d'environnement AWIN_API_TOKEN),
jamais codé en dur.
"""

from __future__ import annotations

import time
from urllib.parse import quote, urlparse

import httpx

from app.core.config import get_settings
from app.core.logging import get_logger
from app.core.observability import outbound_trace_headers, traced_dependency

log = get_logger("awin")

# Cache mémoire : domaine normalisé -> identifiant annonceur (MID Awin).
_DOMAIN_TO_MID: dict[str, int] = {}
_NAME_TO_MID: dict[str, int] = {}
_last_sync: float = 0.0
_SYNC_TTL = 6 * 3600  # 6 h


def _norm_domain(host: str) -> str:
    host = (host or "").lower().strip()
    if host.startswith("www."):
        host = host[4:]
    return host


def _domain_of(url: str) -> str:
    try:
        return _norm_domain(urlparse(url).netloc)
    except Exception:
        return ""


def _registrable(domain: str) -> str:
    """coolblue.be -> coolblue ; amazon.com.be -> amazon (clé de rapprochement souple)."""
    parts = _norm_domain(domain).split(".")
    return parts[0] if parts else ""


async def ensure_advertisers(*, force: bool = False) -> None:
    """Peuple le cache des annonceurs inscrits depuis l'API Awin (si token présent)."""
    global _last_sync
    s = get_settings()
    if not s.awin_api_token or not s.awin_publisher_id:
        return
    if not force and (time.time() - _last_sync) < _SYNC_TTL and _DOMAIN_TO_MID:
        return

    url = f"{s.awin_api_base}/publishers/{s.awin_publisher_id}/programmes"
    headers = {"Authorization": f"Bearer {s.awin_api_token}"}
    params = {"relationship": "joined"}
    try:
        async with traced_dependency("awin", "programmes"):
            headers.update(outbound_trace_headers())
            async with httpx.AsyncClient(timeout=s.llm_timeout_seconds) as client:
                resp = await client.get(url, headers=headers, params=params)
                resp.raise_for_status()
                data = resp.json()
    except Exception as exc:  # pragma: no cover - dépend du réseau/compte
        log.warning(
            "Awin indisponible ou aucun programme (error_type=%s) → liens directs",
            type(exc).__name__,
        )
        _last_sync = time.time()  # évite de marteler l'API en cas d'erreur
        return

    programmes = data if isinstance(data, list) else data.get("programmes", [])
    dmap: dict[str, int] = {}
    nmap: dict[str, int] = {}
    for p in programmes:
        mid = p.get("id")
        if not isinstance(mid, int):
            continue
        name = str(p.get("name") or "").lower().strip()
        if name:
            nmap[name] = mid
            nmap[_registrable(name.replace(" ", ""))] = mid
        # domaines : displayUrl + validDomains
        domains: list[str] = []
        disp = p.get("displayUrl") or p.get("clickThroughUrl")
        if disp:
            domains.append(_domain_of(disp) or _norm_domain(str(disp)))
        for vd in p.get("validDomains") or []:
            d = vd.get("domain") if isinstance(vd, dict) else vd
            if d:
                domains.append(_norm_domain(str(d)))
        for d in domains:
            if d:
                dmap[d] = mid
                dmap[_registrable(d)] = mid

    _DOMAIN_TO_MID.clear(); _DOMAIN_TO_MID.update(dmap)
    _NAME_TO_MID.clear(); _NAME_TO_MID.update(nmap)
    _last_sync = time.time()
    log.info("Awin : %d annonceurs inscrits synchronisés", len(programmes))


def _find_mid(url: str | None, merchant: str | None) -> int | None:
    """Rapproche un produit d'un annonceur Awin inscrit (par domaine puis par nom)."""
    if url:
        dom = _domain_of(url)
        if dom and dom in _DOMAIN_TO_MID:
            return _DOMAIN_TO_MID[dom]
        reg = _registrable(dom)
        if reg and reg in _DOMAIN_TO_MID:
            return _DOMAIN_TO_MID[reg]
    if merchant:
        m = merchant.lower().strip()
        if m in _NAME_TO_MID:
            return _NAME_TO_MID[m]
        key = _registrable(m.replace(" ", ""))
        if key and key in _NAME_TO_MID:
            return _NAME_TO_MID[key]
    return None


def affiliate_link(url: str | None, merchant: str | None = None) -> str | None:
    """Deep-link Awin si le marchand est un annonceur inscrit, sinon le lien direct."""
    if not url:
        return url
    s = get_settings()
    if not s.awin_api_token or not s.awin_publisher_id:
        return url
    mid = _find_mid(url, merchant)
    if not mid:
        return url
    ued = quote(url, safe="")
    return (
        f"https://www.awin1.com/cread.php?awinmid={mid}"
        f"&awinaffid={s.awin_publisher_id}&clickref={s.awin_clickref}&ued={ued}"
    )
