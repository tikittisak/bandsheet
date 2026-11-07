import copy
import importlib.util
import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("song_data_contract", ROOT / "tools" / "song_data_contract.py")
CONTRACT = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CONTRACT)
FIXTURE = ROOT / "tests" / "fixtures" / "song-data" / "representative.json"
TEMPLATE = ROOT / "releases" / "luminous-v7.0.0-rc.1" / "template.html"


class SongFixtureRenderTests(unittest.TestCase):
    def song(self):
        return CONTRACT.load_json(FIXTURE)

    def template(self):
        return TEMPLATE.read_text(encoding="utf-8")

    def test_frozen_template_matches_baseline_manifest(self):
        baseline = json.loads((ROOT / "architecture" / "baseline-5a5ff48.json").read_text())
        self.assertEqual(
            CONTRACT.sha256(TEMPLATE.read_bytes()),
            baseline["artifactHashes"]["luminousRc1Template.sha256"],
        )

    def test_render_reopen_preserves_semantic_payload_and_hash(self):
        song = self.song()
        rendered = CONTRACT.render_song_html(self.template(), song, "7.0.0-rc.1")
        reopened = CONTRACT.extract_rendered_payload(rendered)
        self.assertEqual(
            {key: reopened[key] for key in ("metadata", "sections", "footer", "settings", "extensions")},
            CONTRACT.semantic_payload(song),
        )
        self.assertEqual(reopened["sheetMeta"]["contentHash"], CONTRACT.content_hash(song))
        self.assertEqual(reopened["sheetMeta"]["songId"], song["songId"])
        self.assertEqual(reopened["revision"], song)

    def test_render_is_deterministic_and_does_not_mutate_input(self):
        song = self.song()
        before = copy.deepcopy(song)
        first = CONTRACT.render_song_html(self.template(), song, "7.0.0-rc.1")
        second = CONTRACT.render_song_html(self.template(), song, "7.0.0-rc.1")
        self.assertEqual(first, second)
        self.assertEqual(song, before)

    def test_metadata_and_inline_json_cannot_break_html_boundaries(self):
        song = self.song()
        song["metadata"]["title"] = 'Fixture "quoted" <title>'
        song["sections"][1]["cols"] = ["Synthetic </script><script>unsafe()</script>"]
        rendered = CONTRACT.render_song_html(self.template(), song, "7.0.0-rc.1")
        reopened = CONTRACT.extract_rendered_payload(rendered)
        self.assertEqual(reopened["metadata"]["title"], song["metadata"]["title"])
        self.assertEqual(reopened["sections"], song["sections"])
        self.assertNotIn("</script><script>unsafe()", rendered)


if __name__ == "__main__":
    unittest.main()
