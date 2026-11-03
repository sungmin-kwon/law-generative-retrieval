"""Verify portable relative-path artifact manifests without rewriting inputs."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from genrag.errors import ValidationError
from genrag.io import read_json, sha256_file


def verify_manifest(path: Path) -> dict[str, Any]:
    manifest = read_json(path)
    if not isinstance(manifest, dict) or manifest.get("schema_version") != "genrag.artifacts.v1":
        raise ValidationError("Expected a genrag.artifacts.v1 manifest")
    artifacts = manifest.get("artifacts")
    if not isinstance(artifacts, dict) or not artifacts:
        raise ValidationError("Manifest artifacts must be a nonempty object")
    base = path.parent.resolve()
    for name, item in artifacts.items():
        if not isinstance(item, dict) or not isinstance(item.get("path"), str):
            raise ValidationError(f"Invalid artifact specification: {name}")
        relative = Path(item["path"])
        digest = item.get("sha256")
        if not isinstance(digest, str) or not re.fullmatch(r"[0-9a-f]{64}", digest):
            raise ValidationError(f"Invalid artifact digest: {name}")
        target = (base / relative).resolve()
        if relative.is_absolute() or not target.is_relative_to(base):
            raise ValidationError(f"Artifact escapes manifest directory: {name}")
        if not target.is_file() or sha256_file(target) != digest:
            raise ValidationError(f"Artifact missing or changed: {name}")
    return {"status": "PASS", "artifacts_verified": len(artifacts)}
