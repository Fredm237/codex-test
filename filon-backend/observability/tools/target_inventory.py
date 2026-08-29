"""Compile un inventaire Prometheus de réplicas de façon atomique.

L’entrée et la sortie suivent le format ``file_sd`` de Prometheus. Le
compilateur ajoute cependant les contraintes d’exploitation que le format
générique ne peut pas exprimer : une cible DNS par réplica, labels fermés,
identités uniques et cardinalité attendue explicitement fournie par la
plateforme. Aucune adresse de cible n’est imprimée par la commande.
"""

from __future__ import annotations

import argparse
import hashlib
import ipaddress
import json
import os
import re
import sys
import tempfile
from pathlib import Path
from typing import Any


MAX_TARGET_GROUPS = 100
MAX_SOURCE_BYTES = 1024 * 1024
REQUIRED_LABELS = ("environment", "cluster", "replica")
_LABEL_PATTERN = re.compile(r"^[a-z0-9](?:[a-z0-9._-]{0,62}[a-z0-9])?$")
_DNS_LABEL_PATTERN = re.compile(r"^[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?$")


class TargetInventoryError(ValueError):
    """Erreur sûre de contrat, sans reprise de la valeur fournie."""


def _label(value: Any, *, group_index: int, name: str) -> str:
    if not isinstance(value, str) or not _LABEL_PATTERN.fullmatch(value):
        raise TargetInventoryError(
            f"group {group_index}: label {name} must use the closed lowercase format"
        )
    return value


def _target(value: Any, *, group_index: int) -> str:
    if not isinstance(value, str):
        raise TargetInventoryError(f"group {group_index}: target must be a string")
    if any(marker in value for marker in ("/", "?", "#", "@")):
        raise TargetInventoryError(
            f"group {group_index}: target must be a secret-free DNS host and port"
        )
    if value.count(":") != 1:
        raise TargetInventoryError(
            f"group {group_index}: target must contain exactly one DNS host and port"
        )
    host, port_text = value.rsplit(":", 1)
    host = host.lower()
    if (
        len(host) > 253
        or host == "localhost"
        or host.endswith(".")
        or not any(character.isalpha() for character in host)
    ):
        raise TargetInventoryError(f"group {group_index}: target host is not eligible")
    labels = host.split(".")
    if not labels or any(not _DNS_LABEL_PATTERN.fullmatch(part) for part in labels):
        raise TargetInventoryError(f"group {group_index}: target host is not valid DNS")
    try:
        ipaddress.ip_address(host)
    except ValueError:
        pass
    else:
        raise TargetInventoryError(
            f"group {group_index}: literal IP targets are not accepted"
        )
    if not port_text.isascii() or not port_text.isdigit():
        raise TargetInventoryError(f"group {group_index}: target port is invalid")
    port = int(port_text)
    if not 1 <= port <= 65535:
        raise TargetInventoryError(f"group {group_index}: target port is invalid")
    return f"{host}:{port}"


def normalize_inventory(
    value: Any,
    *,
    expected_replicas: int | None,
    allow_empty: bool = False,
) -> list[dict[str, Any]]:
    """Valide et rend l’inventaire dans un ordre canonique.

    ``allow_empty`` sert uniquement à produire l’état désactivé. Une
    activation non vide exige toujours ``expected_replicas`` afin de ne pas
    confondre un inventaire partiel avec la totalité des processus.
    """

    if not isinstance(value, list):
        raise TargetInventoryError("inventory root must be a list")
    if len(value) > MAX_TARGET_GROUPS:
        raise TargetInventoryError("inventory exceeds the configured target limit")
    if not value:
        if not allow_empty:
            raise TargetInventoryError("empty inventory requires explicit disabled mode")
        if expected_replicas not in (None, 0):
            raise TargetInventoryError("disabled inventory cannot declare replicas")
        return []
    if allow_empty:
        raise TargetInventoryError("disabled mode accepts only an empty inventory")
    if (
        not isinstance(expected_replicas, int)
        or isinstance(expected_replicas, bool)
        or expected_replicas < 1
        or expected_replicas > MAX_TARGET_GROUPS
    ):
        raise TargetInventoryError(
            "non-empty inventory requires an expected replica count"
        )
    if len(value) != expected_replicas:
        raise TargetInventoryError("inventory does not match expected replica count")

    normalized: list[dict[str, Any]] = []
    seen_targets: set[str] = set()
    seen_replicas: set[tuple[str, str, str]] = set()
    for index, group in enumerate(value):
        if not isinstance(group, dict) or set(group) != {"targets", "labels"}:
            raise TargetInventoryError(
                f"group {index}: only targets and labels are accepted"
            )
        targets = group["targets"]
        labels = group["labels"]
        if not isinstance(targets, list) or len(targets) != 1:
            raise TargetInventoryError(
                f"group {index}: exactly one target is required per replica"
            )
        if not isinstance(labels, dict) or set(labels) != set(REQUIRED_LABELS):
            raise TargetInventoryError(
                f"group {index}: labels must be exactly environment, cluster and replica"
            )
        target = _target(targets[0], group_index=index)
        closed_labels = {
            name: _label(labels[name], group_index=index, name=name)
            for name in REQUIRED_LABELS
        }
        identity = tuple(closed_labels[name] for name in REQUIRED_LABELS)
        if target in seen_targets:
            raise TargetInventoryError(f"group {index}: duplicate target")
        if identity in seen_replicas:
            raise TargetInventoryError(f"group {index}: duplicate replica identity")
        seen_targets.add(target)
        seen_replicas.add(identity)
        normalized.append({"targets": [target], "labels": closed_labels})

    normalized.sort(
        key=lambda item: (
            item["labels"]["environment"],
            item["labels"]["cluster"],
            item["labels"]["replica"],
            item["targets"][0],
        )
    )
    return normalized


def canonical_payload(value: Any) -> bytes:
    """Sérialise une preuve JSON validée de façon déterministe."""

    return (
        json.dumps(value, ensure_ascii=True, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")


def inventory_fingerprint(payload: bytes) -> str:
    return f"sha256:{hashlib.sha256(payload).hexdigest()}"


def load_source(path: Path) -> Any:
    try:
        size = path.stat().st_size
    except OSError as exc:
        raise TargetInventoryError("source inventory cannot be inspected") from exc
    if size > MAX_SOURCE_BYTES:
        raise TargetInventoryError("source inventory exceeds the size limit")
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise TargetInventoryError("source inventory is not readable JSON") from exc


def atomic_write(path: Path, payload: bytes) -> None:
    """Remplace le fichier en un rename et synchronise fichier puis dossier."""

    parent = path.parent
    if not parent.is_dir():
        raise TargetInventoryError("output directory does not exist")
    descriptor = -1
    temporary: str | None = None
    try:
        descriptor, temporary = tempfile.mkstemp(
            prefix=f".{path.name}.", suffix=".tmp", dir=parent
        )
        os.fchmod(descriptor, 0o640)
        with os.fdopen(descriptor, "wb") as stream:
            descriptor = -1
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
        temporary = None
        directory_fd = os.open(parent, os.O_RDONLY)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
    except OSError as exc:
        raise TargetInventoryError("target inventory could not be replaced") from exc
    finally:
        if descriptor >= 0:
            os.close(descriptor)
        if temporary is not None:
            try:
                os.unlink(temporary)
            except FileNotFoundError:
                pass


def compile_inventory(
    source: Path,
    output: Path,
    *,
    expected_replicas: int | None,
    allow_empty: bool = False,
) -> tuple[int, str]:
    inventory = normalize_inventory(
        load_source(source),
        expected_replicas=expected_replicas,
        allow_empty=allow_empty,
    )
    payload = canonical_payload(inventory)
    atomic_write(output, payload)
    return len(inventory), inventory_fingerprint(payload)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Compile a strict Prometheus replica inventory atomically."
    )
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--expected-replicas", type=int)
    mode.add_argument("--allow-empty", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        count, fingerprint = compile_inventory(
            args.source,
            args.output,
            expected_replicas=args.expected_replicas,
            allow_empty=args.allow_empty,
        )
    except TargetInventoryError as exc:
        print(f"target inventory rejected: {exc}", file=sys.stderr)
        return 2
    print(f"target_groups={count} fingerprint={fingerprint}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
