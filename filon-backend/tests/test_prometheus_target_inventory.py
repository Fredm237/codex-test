from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from observability.tools.target_inventory import (
    TargetInventoryError,
    compile_inventory,
    normalize_inventory,
)


ROOT = Path(__file__).resolve().parents[1]
SCHEMA = (
    ROOT
    / "observability"
    / "schemas"
    / "prometheus-target-inventory.schema.json"
)


def _group(
    target: str = "replica-a.internal.example:443",
    *,
    environment: str = "production",
    cluster: str = "filon-eu",
    replica: str = "replica-a",
) -> dict[str, object]:
    return {
        "targets": [target],
        "labels": {
            "environment": environment,
            "cluster": cluster,
            "replica": replica,
        },
    }


def test_normalizes_one_target_per_replica_deterministically():
    value = [
        _group(
            "replica-b.internal.example:443",
            replica="replica-b",
        ),
        _group(),
    ]
    assert normalize_inventory(value, expected_replicas=2) == [
        _group(),
        _group(
            "replica-b.internal.example:443",
            replica="replica-b",
        ),
    ]


def test_inventory_schema_is_draft_2020_closed_and_matches_canonical_shape():
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"
    assert schema["type"] == "array"
    assert schema["maxItems"] == 100
    group = schema["items"]
    assert group["additionalProperties"] is False
    assert set(group["required"]) == {"targets", "labels"}
    assert group["properties"]["targets"]["minItems"] == 1
    assert group["properties"]["targets"]["maxItems"] == 1
    labels = group["properties"]["labels"]
    assert labels["additionalProperties"] is False
    assert set(labels["required"]) == {"environment", "cluster", "replica"}
    Draft202012Validator(schema).validate([_group()])

@pytest.mark.parametrize(
    ("value", "expected", "allow_empty"),
    [
        ({}, 1, False),
        ([], None, False),
        ([_group()], None, False),
        ([_group()], 2, False),
        ([_group()], 1, True),
        ([_group("https://replica.internal.example:443")], 1, False),
        ([_group("replica.internal.example:443/path")], 1, False),
        ([_group("127.0.0.1:443")], 1, False),
        ([_group("127.000.000.001:443")], 1, False),
        ([_group("localhost:443")], 1, False),
        ([_group("replica.internal.example:0")], 1, False),
        ([_group("replica.internal.example:65536")], 1, False),
        ([_group(environment="Production")], 1, False),
        ([_group(replica="-replica")], 1, False),
        (
            [
                {
                    **_group(),
                    "token": "must-not-be-accepted",
                }
            ],
            1,
            False,
        ),
        (
            [
                {
                    "targets": ["replica-a.internal.example:443"],
                    "labels": {
                        **_group()["labels"],
                        "region": "eu",
                    },
                }
            ],
            1,
            False,
        ),
        (
            [
                {
                    "targets": [
                        "replica-a.internal.example:443",
                        "replica-b.internal.example:443",
                    ],
                    "labels": _group()["labels"],
                }
            ],
            1,
            False,
        ),
        ([_group(), _group()], 2, False),
        (
            [
                _group(),
                _group(
                    "replica-b.internal.example:443",
                ),
            ],
            2,
            False,
        ),
    ],
)
def test_rejects_partial_ambiguous_or_secret_bearing_inventory(
    value: object,
    expected: int | None,
    allow_empty: bool,
):
    with pytest.raises(TargetInventoryError):
        normalize_inventory(
            value,
            expected_replicas=expected,
            allow_empty=allow_empty,
        )


def test_empty_inventory_requires_and_accepts_explicit_disabled_mode():
    assert normalize_inventory([], expected_replicas=None, allow_empty=True) == []


def test_compile_is_atomic_canonical_and_restricts_permissions(tmp_path: Path):
    source = tmp_path / "source.json"
    output = tmp_path / "targets.json"
    source.write_text(json.dumps([_group()]), encoding="utf-8")

    count, fingerprint = compile_inventory(
        source,
        output,
        expected_replicas=1,
    )

    assert count == 1
    assert fingerprint.startswith("sha256:")
    assert len(fingerprint) == 71
    assert json.loads(output.read_text(encoding="utf-8")) == [_group()]
    assert (os.stat(output).st_mode & 0o777) == 0o640
    assert not list(tmp_path.glob(".targets.json.*.tmp"))


def test_rejected_source_never_replaces_previous_inventory(tmp_path: Path):
    source = tmp_path / "source.json"
    output = tmp_path / "targets.json"
    output.write_text("previous-proof\n", encoding="utf-8")
    source.write_text(json.dumps([_group("private.example:443/path")]), encoding="utf-8")

    with pytest.raises(TargetInventoryError):
        compile_inventory(source, output, expected_replicas=1)

    assert output.read_text(encoding="utf-8") == "previous-proof\n"
    assert not list(tmp_path.glob(".targets.json.*.tmp"))


def test_cli_reports_only_count_and_fingerprint(tmp_path: Path):
    source = tmp_path / "source.json"
    output = tmp_path / "targets.json"
    source.write_text(json.dumps([_group()]), encoding="utf-8")

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "observability.tools.target_inventory",
            str(source),
            str(output),
            "--expected-replicas",
            "1",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert result.stderr == ""
    assert result.stdout.startswith("target_groups=1 fingerprint=sha256:")
    assert "replica-a" not in result.stdout
    assert "internal.example" not in result.stdout


def test_cli_rejection_does_not_echo_internal_target(tmp_path: Path):
    source = tmp_path / "source.json"
    output = tmp_path / "targets.json"
    secret_host = "sensitive-replica.private.example:443/path"
    source.write_text(json.dumps([_group(secret_host)]), encoding="utf-8")

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "observability.tools.target_inventory",
            str(source),
            str(output),
            "--expected-replicas",
            "1",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 2
    assert not output.exists()
    assert secret_host not in result.stderr
    assert "target inventory rejected" in result.stderr
