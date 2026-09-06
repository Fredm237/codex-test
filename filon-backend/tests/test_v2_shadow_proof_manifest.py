from __future__ import annotations

import hashlib
import json
from datetime import datetime
from pathlib import Path

from app.v2_chain.proof_registry import SHADOW_PROOF_KEYS, _validated_values


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
MANIFEST_PATH = (
    REPOSITORY_ROOT
    / "docs"
    / "architecture"
    / "V2_SHADOW_PROMOTION_PROOF_MANIFEST.json"
)


def test_shadow_promotion_proof_manifest_is_complete_and_reproducible() -> None:
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))

    assert manifest["schema_version"] == (
        "filon-v2-shadow-promotion-proof-manifest/v1"
    )
    assert manifest["raw_payload_retained"] is False
    assert manifest["verification_status"] == "VERIFIED"

    proofs = manifest["proofs"]
    assert {proof["proof_kind"] for proof in proofs} == SHADOW_PROOF_KEYS
    assert len(proofs) == len(SHADOW_PROOF_KEYS)

    verified_at = datetime.fromisoformat(manifest["verified_at"].replace("Z", "+00:00"))
    for proof in proofs:
        artifact_locator = proof["artifact_ref"].removeprefix("doc:")
        artifact_path = artifact_locator.partition("#")[0]
        artifact_bytes = (REPOSITORY_ROOT / artifact_path).read_bytes()
        artifact_digest = "sha256:" + hashlib.sha256(artifact_bytes).hexdigest()
        assert artifact_digest == proof["artifact_digest"]

        values = _validated_values(
            scope_ref=manifest["scope_ref"],
            proof_kind=proof["proof_kind"],
            artifact_ref=proof["artifact_ref"],
            artifact_digest=proof["artifact_digest"],
            verifier_version=manifest["verifier_version"],
            verification_status=manifest["verification_status"],
            verified_at=verified_at,
        )
        assert values["proof_ref"] == proof["proof_ref"]
