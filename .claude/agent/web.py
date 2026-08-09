#!/usr/bin/env python3
"""Accès web unifié — une seule porte, un ordre de repli imposé.

L'environnement a plusieurs voies vers le web et elles n'ont pas les mêmes
droits. Les essayer au hasard fait perdre du temps et produit des conclusions
fausses (« le site est mort » alors que c'est l'outil qui est bloqué). Ce
module impose l'ordre, mémorise ce qui est définitivement fermé, et dit
toujours **par quelle voie** le résultat est arrivé.

Ce qui a été mesuré sur cet environnement, et qui fonde l'ordre :

  - `curl` passe par $HTTPS_PROXY et fonctionne ;
  - Chromium local est coupé par la politique d'egress (ERR_CONNECTION_RESET),
    y compris à travers le proxy — on ne contourne pas, c'est une règle ;
  - Firecrawl fonctionne, sauf refus de politique explicite (Instagram) ;
  - Apify est la seule voie qui atteint Instagram ;
  - le port du proxy est DYNAMIQUE : toujours lire $HTTPS_PROXY.

Aucune clé n'est jamais affichée ni journalisée.

    python3 .claude/agent/web.py lire https://exemple.be
    python3 .claude/agent/web.py chercher "cashback belgique 2026"
    python3 .claude/agent/web.py social https://www.instagram.com/w.wearebrand/
    python3 .claude/agent/web.py etat
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
import urllib.parse

TEMPS = 60

# Refus de politique constatés : les réessayer ne fait que perdre du temps.
FERME = {
    ("firecrawl", "instagram.com"): "Firecrawl refuse Instagram (politique, pas un incident)",
    ("navigateur", "*"): "Chromium local est coupé par la politique d'egress",
}


def _cle(nom: str) -> str | None:
    return os.environ.get(nom) or None


def _hote(url: str) -> str:
    try:
        return urllib.parse.urlparse(url).netloc.lower().removeprefix("www.")
    except Exception:
        return ""


def _ferme(voie: str, url: str) -> str | None:
    h = _hote(url)
    for (v, motif), raison in FERME.items():
        if v == voie and (motif == "*" or motif in h):
            return raison
    return None


def _curl(url: str, entete: dict | None = None, donnees: str | None = None,
          methode: str = "GET") -> tuple[int, str]:
    """Un seul appel réseau, via curl : c'est la voie qui respecte le proxy."""
    cmd = ["curl", "-sS", "--max-time", str(TEMPS), "-X", methode,
           "-w", "\n__CODE__%{http_code}", url]
    for k, v in (entete or {}).items():
        cmd += ["-H", f"{k}: {v}"]
    if donnees:
        cmd += ["-d", donnees]
    r = subprocess.run(cmd, capture_output=True, text=True)
    sortie = r.stdout
    code = 0
    if "__CODE__" in sortie:
        sortie, _, brut = sortie.rpartition("\n__CODE__")
        code = int(brut.strip() or 0)
    return code, sortie


def _reessaye(fn, tentatives: int = 3):
    """RETRY : trois essais, attente croissante. Un 4xx ne se réessaie pas."""
    dernier = None
    for i in range(tentatives):
        try:
            code, corps = fn()
            if 200 <= code < 300:
                return code, corps
            if 400 <= code < 500 and code not in (408, 429):
                return code, corps  # définitif : inutile d'insister
            dernier = (code, corps)
        except Exception as e:  # noqa: BLE001
            dernier = (0, str(e))
        time.sleep(2 ** i)
    return dernier or (0, "")


# ── voies ────────────────────────────────────────────────────────────────


def via_firecrawl(url: str) -> tuple[bool, str, str]:
    raison = _ferme("firecrawl", url)
    if raison:
        return False, "firecrawl", raison
    cle = _cle("FIRECRAWL_API_KEY")
    if not cle:
        return False, "firecrawl", "FIRECRAWL_API_KEY absente"
    code, corps = _reessaye(lambda: _curl(
        "https://api.firecrawl.dev/v2/scrape",
        {"Authorization": f"Bearer {cle}", "Content-Type": "application/json"},
        json.dumps({"url": url, "formats": ["markdown"]}), "POST"))
    if code == 200:
        try:
            d = json.loads(corps)
            md = (d.get("data") or {}).get("markdown") or ""
            if md.strip():
                return True, "firecrawl", md
        except json.JSONDecodeError:
            pass
    detail = ""
    try:
        detail = json.loads(corps).get("error", "")[:160]
    except Exception:  # noqa: BLE001
        detail = corps[:160]
    return False, "firecrawl", f"HTTP {code} {detail}"


def via_curl(url: str) -> tuple[bool, str, str]:
    """FALLBACK : le HTML brut. Sans rendu JS, mais souvent suffisant."""
    code, corps = _reessaye(lambda: _curl(url, {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                      "(KHTML, like Gecko) Chrome/126.0 Safari/537.36"}))
    if code == 200 and corps.strip():
        return True, "curl", corps
    return False, "curl", f"HTTP {code}"


def via_apify(url: str) -> tuple[bool, str, str]:
    """RECOVERY réseaux sociaux : la seule voie qui atteint Instagram."""
    jeton = _cle("APIFY_TOKEN") or _cle("APIFY_API_TOKEN")
    if not jeton:
        return False, "apify", "APIFY_TOKEN absent de l'environnement"
    acteur = ("apify~instagram-profile-scraper"
              if "instagram.com" in _hote(url) else "apify~website-content-crawler")
    if acteur.endswith("instagram-profile-scraper"):
        nom = url.rstrip("/").split("/")[-1]
        charge = json.dumps({"usernames": [nom]})
    else:
        charge = json.dumps({"startUrls": [{"url": url}], "maxCrawlPages": 1})
    code, corps = _reessaye(lambda: _curl(
        f"https://api.apify.com/v2/acts/{acteur}/run-sync-get-dataset-items?token={jeton}",
        {"Content-Type": "application/json"}, charge, "POST"), tentatives=2)
    if code in (200, 201) and corps.strip():
        return True, "apify", corps
    return False, "apify", f"HTTP {code}"


def via_recherche(requete: str) -> tuple[bool, str, str]:
    cle = _cle("FIRECRAWL_API_KEY")
    if not cle:
        return False, "firecrawl_search", "FIRECRAWL_API_KEY absente"
    code, corps = _reessaye(lambda: _curl(
        "https://api.firecrawl.dev/v2/search",
        {"Authorization": f"Bearer {cle}", "Content-Type": "application/json"},
        json.dumps({"query": requete, "limit": 8}), "POST"))
    if code == 200:
        return True, "firecrawl_search", corps
    return False, "firecrawl_search", f"HTTP {code}"


# ── commandes ────────────────────────────────────────────────────────────


def cmd_lire(a) -> None:
    for voie in (via_firecrawl, via_curl, via_apify):
        ok, nom, res = voie(a.url)
        if ok:
            print(f"[voie: {nom}]", file=sys.stderr)
            print(res[: a.max])
            return
        print(f"[{nom} → échec: {res}]", file=sys.stderr)
    sys.exit("Toutes les voies ont échoué. Voir les raisons ci-dessus.")


def cmd_chercher(a) -> None:
    ok, nom, res = via_recherche(a.requete)
    print(f"[voie: {nom}]", file=sys.stderr)
    if not ok:
        sys.exit(f"Recherche impossible : {res}")
    print(res[: a.max])


def cmd_social(a) -> None:
    ok, nom, res = via_apify(a.url)
    print(f"[voie: {nom}]", file=sys.stderr)
    if not ok:
        sys.exit(f"Échec : {res}")
    print(res[: a.max])


def cmd_etat(a) -> None:
    """Teste réellement chaque voie. Ne suppose rien."""
    print("Proxy      :", os.environ.get("HTTPS_PROXY", "(absent)"))
    for nom, var in (("FIRECRAWL_API_KEY", "FIRECRAWL_API_KEY"),
                     ("APIFY_TOKEN", "APIFY_TOKEN")):
        print(f"{nom:<11}: {'présente' if _cle(var) else 'ABSENTE'}")
    print("\nSondes réelles :")
    ok, _, _ = via_curl("https://example.com")
    print(f"  curl externe      : {'OK' if ok else 'ÉCHEC'}")
    ok, _, det = via_firecrawl("https://example.com")
    print(f"  firecrawl         : {'OK' if ok else 'ÉCHEC — ' + det[:60]}")
    print("  navigateur local  : COUPÉ (politique d'egress — ne pas contourner)")
    for (v, m), r in FERME.items():
        print(f"  fermé: {v}/{m} — {r}")


def main() -> None:
    p = argparse.ArgumentParser(description="Accès web unifié, avec repli")
    p.add_argument("--max", type=int, default=20000, help="troncature de sortie")
    s = p.add_subparsers(dest="cmd", required=True)

    q = s.add_parser("lire", help="lire une page (firecrawl → curl → apify)")
    q.add_argument("url")
    q.set_defaults(f=cmd_lire)

    q = s.add_parser("chercher", help="rechercher sur le web")
    q.add_argument("requete")
    q.set_defaults(f=cmd_chercher)

    q = s.add_parser("social", help="réseaux sociaux (Apify)")
    q.add_argument("url")
    q.set_defaults(f=cmd_social)

    q = s.add_parser("etat", help="sonder réellement chaque voie")
    q.set_defaults(f=cmd_etat)

    a = p.parse_args()
    a.f(a)


if __name__ == "__main__":
    main()
