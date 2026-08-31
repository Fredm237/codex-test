"""Détermine si un changement doit franchir le gate Quality strict."""

from __future__ import annotations

import argparse
import sys
from collections.abc import Iterable


ENGINE_PREFIXES = (
    "contracts/",
    "filon-backend/app/intelligence/",
    "filon-backend/app/agents/",
    "filon-backend/app/llm/",
    "filon-backend/app/observations/",
)
ENGINE_FILES = frozenset(
    {
        "filon-backend/app/api/routes/advise.py",
        "filon-backend/app/api/routes/catalog.py",
        "filon-backend/app/api/routes/intelligence.py",
        "filon-backend/app/api/routes/stream.py",
        "filon-backend/app/data/catalog.py",
        "filon-backend/app/schemas/advise.py",
        "filon-backend/app/services/awin.py",
        "filon-backend/app/services/awin_catalog.py",
        "filon-backend/app/services/catalog_grouping.py",
        "filon-backend/app/services/catalog_paging.py",
        "filon-backend/app/services/catalog_search.py",
        "filon-backend/app/services/catalog_source.py",
        "filon-backend/app/services/coherence.py",
        "filon-backend/app/services/currency.py",
        "filon-backend/app/services/decision.py",
        "filon-backend/app/services/dedup.py",
        "filon-backend/app/services/freshness.py",
        "filon-backend/app/services/offer_evidence.py",
        "filon-backend/app/services/product_role.py",
        "filon-backend/app/services/recommend.py",
        "filon-backend/app/services/relevance.py",
        "filon-backend/app/services/search.py",
        "filon-backend/app/services/serpapi_shopping.py",
        "filon-backend/app/services/source_normalization.py",
        "filon-backend/app/services/taxonomy.py",
        "filon-backend/app/services/vectorstore.py",
        "filon-backend/app/services/verdict.py",
    }
)


def normalize_changed_paths(paths: Iterable[str]) -> tuple[str, ...]:
    return tuple(
        path.strip().replace("\\", "/").removeprefix("./")
        for path in paths
        if path.strip()
    )


def quality_gate_paths(paths: Iterable[str]) -> tuple[str, ...]:
    changed = normalize_changed_paths(paths)
    return tuple(
        path
        for path in changed
        if path in ENGINE_FILES or path.startswith(ENGINE_PREFIXES)
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Détecte les changements du moteur soumis au Quality gate strict"
    )
    parser.add_argument("paths", nargs="*")
    args = parser.parse_args()
    paths = args.paths or sys.stdin.read().splitlines()
    gated = quality_gate_paths(paths)
    print(f"quality_gate_required={'true' if gated else 'false'}")
    print(f"quality_gate_path_count={len(gated)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
