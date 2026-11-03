"""Create a reviewed public tree from an explicit allowlist, never a workspace copy."""

from __future__ import annotations

import re
import shutil
import tempfile
from pathlib import Path
from typing import Any

from genrag.errors import ValidationError
from genrag.io import atomic_json, sha256_file

PUBLIC_FILES = (
    "README.md",
    "pyproject.toml",
    "MANIFEST.in",
    "NOTICE.md",
    "LICENSE",
    "CONTRIBUTING.md",
    "SECURITY.md",
    ".gitignore",
    ".gitattributes",
    ".editorconfig",
    ".github/workflows/ci.yml",
    ".github/ISSUE_TEMPLATE/bug_report.yml",
    ".github/pull_request_template.md",
    "docs/architecture.md",
    "docs/research-design.md",
    "docs/dataset-reproducibility.md",
    "docs/getting-started.md",
    "docs/evaluation.md",
    "docs/development.md",
    "docs/publishing.md",
    "src/genrag/data/korean_tax_rulings.json",
)
PUBLIC_TREES = {
    "src/genrag": {".py", ".typed"},
    "tests/public": {".py"},
    "examples/synthetic": {".json", ".jsonl", ".md"},
    "examples/korean-tax": {".md"},
    "dataset_specs": {".json", ".md"},
}
SECRET_PATTERNS = {
    "provider API key": re.compile(r"(?:sk-or-v1-[A-Za-z0-9_-]{20,}|AIza[A-Za-z0-9_-]{30,})"),
    "GitHub token": re.compile(r"(?:gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,})"),
    "private key": re.compile(r"-----BEGIN (?:[A-Z]+ )?PRIVATE KEY-----"),
    "AWS access key": re.compile(r"\b(?:AKIA|ASIA)[A-Z0-9]{16}\b"),
}


def public_paths(source: Path) -> tuple[Path, ...]:
    paths = [source / name for name in PUBLIC_FILES]
    for name, suffixes in PUBLIC_TREES.items():
        directory = source / name
        if not directory.is_dir() or directory.is_symlink():
            raise ValidationError(f"Missing or linked public directory: {name}")
        for path in directory.rglob("*"):
            if path.is_symlink():
                raise ValidationError(f"Symlinks are not allowed in the public tree: {name}")
            if path.is_file() and path.suffix in suffixes:
                paths.append(path)
    for path in paths:
        if path.is_symlink() or not path.is_file():
            raise ValidationError(f"Missing or linked public file: {path.relative_to(source)}")
        if not path.resolve().is_relative_to(source):
            raise ValidationError("Public file escapes source directory")
    return tuple(sorted(paths))


def export_public(
    source: Path, destination: Path, *, forbidden_terms: tuple[str, ...] = ()
) -> dict[str, Any]:
    """Validate everything before creating an atomic, secret-screened export.

    This is a targeted screen, not a guarantee that all confidential information
    can be recognized automatically. Human review still precedes publication.
    """
    source, destination = source.resolve(), destination.resolve()
    if destination.exists():
        raise ValidationError("Export destination already exists; refusing to overwrite it")
    if destination.is_relative_to(source):
        raise ValidationError("Export must be outside the source workspace")
    if any(not term.strip() for term in forbidden_terms):
        raise ValidationError("Forbidden terms must be nonempty")
    paths = public_paths(source)
    findings = []
    for path in paths:
        relative = path.relative_to(source).as_posix()
        if path.stat().st_size > 1_000_000:
            raise ValidationError(f"Unexpected large public file: {relative}")
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeError:
            raise ValidationError(f"Non-text public file: {relative}") from None
        if "\x00" in text:
            raise ValidationError(f"Binary content in public file: {relative}")
        for label, pattern in SECRET_PATTERNS.items():
            if pattern.search(text):
                findings.append(f"{relative}: {label}")
        if any(term.casefold() in text.casefold() for term in forbidden_terms):
            findings.append(f"{relative}: forbidden publication term")
    if findings:
        # Only paths and categories are returned, never matched credential values.
        raise ValidationError("Public export blocked: " + "; ".join(findings))
    destination.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=".genrag-export-", dir=destination.parent))
    try:
        artifacts = {}
        for path in paths:
            relative = path.relative_to(source)
            target = staging / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(path, target)
            original = sha256_file(path)
            if sha256_file(target) != original:
                raise ValidationError("Source changed during public export")
            artifacts[relative.as_posix()] = {"path": relative.as_posix(), "sha256": original}
        manifest = {"schema_version": "genrag.artifacts.v1", "artifacts": artifacts}
        atomic_json(staging / "public-export-manifest.json", manifest)
        if destination.exists():
            raise ValidationError("Export destination appeared during preparation")
        staging.rename(destination)
    finally:
        if staging.exists():
            shutil.rmtree(staging)
    return {
        "status": "PASS",
        "exported_files": len(paths),
        "destination": str(destination),
        "manifest": "public-export-manifest.json",
        "publication_performed": False,
    }
