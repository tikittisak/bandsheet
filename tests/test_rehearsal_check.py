import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("rehearsal_check", ROOT / "rehearsal_check.py")
CHECK = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CHECK)


class RehearsalCheckTests(unittest.TestCase):
    def test_unapproved_migration_baseline_is_a_provenance_gap(self):
        audit = CHECK.inspect_song("songs/jesus-of-suburbia.html", {})
        self.assertIn(
            "provenance gap: migration baseline never Ti-approved",
            audit["issues"],
        )
        self.assertIn("no lyric blocks", audit["issues"])

    def test_restored_source_is_not_mislabeled_as_migration_gap(self):
        audit = CHECK.inspect_song("songs/hysteria.html", {})
        self.assertNotIn(
            "provenance gap: migration baseline never Ti-approved",
            audit["issues"],
        )


if __name__ == "__main__":
    unittest.main()
