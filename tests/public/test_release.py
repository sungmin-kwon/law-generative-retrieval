"""Publication boundaries, traversal protection and transactional export behavior."""

import tempfile
import unittest
from pathlib import Path

from genrag.errors import ValidationError
from genrag.integrity import verify_manifest
from genrag.release import PUBLIC_FILES, PUBLIC_TREES, export_public


class ReleaseTests(unittest.TestCase):
    def source(self, root):
        for name in PUBLIC_FILES:
            path = root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("public demonstration\n", encoding="utf-8")
        for name in PUBLIC_TREES:
            (root / name).mkdir(parents=True, exist_ok=True)
        (root / "src/genrag/__init__.py").write_text('"""Example package."""\n')
        (root / ".env").write_text("PRIVATE_VALUE=not-for-export\n")
        (root / "internal-report.md").write_text("private meeting notes\n")

    def test_only_allowlisted_files_are_exported_and_hashes_verify(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "source"
            source.mkdir()
            self.source(source)
            target = Path(tmp) / "public"
            report = export_public(source, target)
            self.assertFalse(report["publication_performed"])
            self.assertFalse((target / ".env").exists())
            self.assertFalse((target / "internal-report.md").exists())
            self.assertEqual(
                verify_manifest(target / "public-export-manifest.json")["status"], "PASS"
            )

    def test_detected_secret_blocks_export_without_echoing_it(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "source"
            source.mkdir()
            self.source(source)
            secret = "sk-or-v1-" + "x" * 45
            (source / "README.md").write_text(secret)
            target = Path(tmp) / "public"
            with self.assertRaises(ValidationError) as caught:
                export_public(source, target)
            self.assertNotIn(secret, str(caught.exception))
            self.assertFalse(target.exists())

    def test_forbidden_terms_and_existing_destinations_are_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "source"
            source.mkdir()
            self.source(source)
            target = Path(tmp) / "public"
            with self.assertRaisesRegex(ValidationError, "forbidden"):
                export_public(source, target, forbidden_terms=("demonstration",))
            target.mkdir()
            sentinel = target / "keep"
            sentinel.write_text("unchanged")
            with self.assertRaisesRegex(ValidationError, "exists"):
                export_public(source, target)
            self.assertEqual(sentinel.read_text(), "unchanged")

    def test_symlink_escape_and_workspace_destination_are_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "source"
            source.mkdir()
            self.source(source)
            with self.assertRaisesRegex(ValidationError, "outside"):
                export_public(source, source / "out")
            outside = Path(tmp) / "outside.py"
            outside.write_text("private content")
            linked = source / "src/genrag/linked.py"
            try:
                linked.symlink_to(outside)
            except OSError:
                self.skipTest("Symlinks unavailable in this environment")
            with self.assertRaisesRegex(ValidationError, "Symlinks"):
                export_public(source, Path(tmp) / "public")


if __name__ == "__main__":
    unittest.main()
