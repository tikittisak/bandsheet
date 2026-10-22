import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("content_guard", ROOT / "content_guard.py")
GUARD = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GUARD)


class ContentGuardTests(unittest.TestCase):
    def test_template_only_changes_do_not_change_payload(self):
        base = (ROOT / "songs" / "starlight.html").read_text(encoding="utf-8")
        changed = base.replace("</style>", ".guard-test{color:red}</style>", 1)
        self.assertEqual(GUARD.content_payload(base), GUARD.content_payload(changed))

    def test_lyric_change_is_detected(self):
        base = (ROOT / "songs" / "starlight.html").read_text(encoding="utf-8")
        changed = base.replace("Our hopes and expectations", "Changed lyric", 1)
        self.assertNotEqual(GUARD.content_payload(base), GUARD.content_payload(changed))

    def test_chord_change_is_detected(self):
        base = (ROOT / "songs" / "starlight.html").read_text(encoding="utf-8")
        changed = base.replace('"c": "E"', '"c": "F"', 1)
        self.assertNotEqual(GUARD.content_payload(base), GUARD.content_payload(changed))

    def test_allowlist_is_exact_song_path(self):
        self.assertEqual(
            GUARD.normalize_allowed(["songs/starlight.html"]),
            {"songs/starlight.html"},
        )
        with self.assertRaises(ValueError):
            GUARD.normalize_allowed(["songs/*.html"])

    def test_content_digest_ignores_json_key_order(self):
        self.assertEqual(
            GUARD.content_digest({"b": 2, "a": 1}),
            GUARD.content_digest({"a": 1, "b": 2}),
        )


if __name__ == "__main__":
    unittest.main()
