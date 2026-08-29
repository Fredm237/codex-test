from __future__ import annotations

import io
import sys

from quality_lab import ci_scope


def test_quality_scope_covers_every_decision_engine_boundary() -> None:
    paths = [
        "filon-backend/app/intelligence/general_decision.py",
        "filon-backend/app/agents/decision.py",
        "filon-backend/app/services/taxonomy.py",
        "filon-backend/app/services/offer_evidence.py",
        "filon-backend/app/api/routes/stream.py",
        "filon-backend/app/observations/awin.py",
        "contracts/v1/catalogue.schema.json",
        "filon-backend/app/services/awin_catalog.py",
    ]

    assert ci_scope.quality_gate_paths(paths) == tuple(paths)


def test_quality_scope_does_not_block_governance_or_unrelated_clients() -> None:
    assert ci_scope.quality_gate_paths(
        [
            "quality/schemas/manifest.schema.json",
            "docs/architecture/PHASE_0_EXECUTION_PLAN.md",
            "filon-backend/tests/test_quality_lab.py",
            "filon-web/app/page.tsx",
            "filon-backend/app/intelligence_future.py",
        ]
    ) == ()


def test_quality_scope_normalizes_git_paths_without_prefix_collisions() -> None:
    assert ci_scope.quality_gate_paths(
        [
            r".\filon-backend\app\services\decision.py",
            "",
            "filon-backend/app/services/decision.py.backup",
        ]
    ) == ("filon-backend/app/services/decision.py",)


def test_cli_emits_stable_github_outputs(monkeypatch, capsys) -> None:
    monkeypatch.setattr(sys, "stdin", io.StringIO("filon-backend/app/services/search.py\n"))
    monkeypatch.setattr(sys, "argv", ["ci-scope"])

    assert ci_scope.main() == 0
    assert capsys.readouterr().out.splitlines() == [
        "quality_gate_required=true",
        "quality_gate_path_count=1",
    ]
