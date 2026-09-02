"""Construit une archive Chrome Web Store minimale et reproductible."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo


ROOT = Path(__file__).resolve().parents[1]
FILES = (
    "_locales/fr/messages.json",
    "background.js",
    "content.css",
    "content.js",
    "icons/icon16.png",
    "icons/icon32.png",
    "icons/icon48.png",
    "icons/icon128.png",
    "manifest.json",
    "popup.html",
    "popup.js",
    "product-observation.js",
)
ZIP_TIMESTAMP = (2026, 9, 2, 0, 0, 0)


def _manifest_references(manifest: dict) -> set[str]:
    references = {
        manifest["background"]["service_worker"],
        manifest["action"]["default_popup"],
    }
    references.update(manifest.get("icons", {}).values())
    references.update(manifest.get("action", {}).get("default_icon", {}).values())
    for content_script in manifest.get("content_scripts", []):
        references.update(content_script.get("js", []))
        references.update(content_script.get("css", []))
    for group in manifest.get("web_accessible_resources", []):
        references.update(group.get("resources", []))
    return references


def build(output: Path) -> str:
    manifest = json.loads((ROOT / "manifest.json").read_text(encoding="utf-8"))
    if manifest.get("manifest_version") != 3:
        raise ValueError("Manifest V3 is required")
    missing_from_package = sorted(_manifest_references(manifest) - set(FILES))
    if missing_from_package:
        raise ValueError(f"manifest references unpackaged files: {missing_from_package}")
    missing_on_disk = [name for name in FILES if not (ROOT / name).is_file()]
    if missing_on_disk:
        raise FileNotFoundError(f"package files are missing: {missing_on_disk}")

    output.parent.mkdir(parents=True, exist_ok=True)
    with ZipFile(output, "w", compression=ZIP_DEFLATED, compresslevel=9) as archive:
        for name in FILES:
            info = ZipInfo(name, date_time=ZIP_TIMESTAMP)
            info.compress_type = ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, (ROOT / name).read_bytes(), compresslevel=9)
    digest = hashlib.sha256(output.read_bytes()).hexdigest()
    return digest


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    digest = build(args.output.resolve())
    print(json.dumps({"archive": args.output.name, "files": len(FILES), "sha256": digest}, sort_keys=True))


if __name__ == "__main__":
    main()
