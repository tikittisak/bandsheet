import copy
import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("song_data_contract", ROOT / "tools" / "song_data_contract.py")
CONTRACT = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CONTRACT)
FIXTURES = ROOT / "tests" / "fixtures"


class SongDataContractTests(unittest.TestCase):
    def song(self):
        return CONTRACT.load_json(FIXTURES / "song-data" / "representative.json")

    def band(self):
        return CONTRACT.load_json(FIXTURES / "catalog" / "band.json")

    def playlist(self):
        return CONTRACT.load_json(FIXTURES / "catalog" / "playlist.json")

    def test_schema_documents_are_valid_json(self):
        names = {path.name for path in (ROOT / "schemas").glob("*.schema.json")}
        self.assertEqual(
            names,
            {"song.schema.json", "band.schema.json", "playlist.schema.json", "catalog.schema.json", "release.schema.json"},
        )
        for path in (ROOT / "schemas").glob("*.schema.json"):
            self.assertEqual(json.loads(path.read_text())["$schema"], "https://json-schema.org/draft/2020-12/schema")

    def test_representative_fixture_and_relationships_validate(self):
        self.assertEqual(CONTRACT.validate_song(self.song())["songId"], "fixture-representative")
        self.assertEqual(CONTRACT.validate_band(self.band())["bandId"], "fixture-band")
        self.assertEqual(CONTRACT.validate_playlist(self.playlist())["playlistId"], "fixture-set")

    def test_content_and_revision_hashes_have_separate_meaning(self):
        original = self.song()
        provenance_change = copy.deepcopy(original)
        provenance_change["provenance"]["note"] = "Different receipt note"
        self.assertEqual(CONTRACT.content_hash(original), CONTRACT.content_hash(provenance_change))
        self.assertNotEqual(CONTRACT.revision_hash(original), CONTRACT.revision_hash(provenance_change))

        musical_change = copy.deepcopy(original)
        musical_change["sections"][0]["bars"][0]["c"] = "Dm"
        self.assertNotEqual(CONTRACT.content_hash(original), CONTRACT.content_hash(musical_change))

    def test_catalog_is_derived_without_song_html(self):
        song = self.song()
        digest = CONTRACT.content_hash(song)
        catalog = CONTRACT.build_catalog(
            [song],
            [self.band()],
            [self.playlist()],
            {song["songId"]: {"contentHash": digest, "approvedOn": "2026-11-06"}},
            index_version="1.0.0-draft.1",
            release_id="fixture-release",
        )
        self.assertEqual(catalog["songs"][0]["approvalStatus"], "approved")
        self.assertEqual(catalog["songs"][0]["href"], "songs/fixture-representative.html")
        self.assertEqual(catalog["songs"][0]["bars"], 2)
        self.assertEqual(catalog["songs"][0]["lyricBlocks"], 1)
        self.assertRegex(catalog["catalogBuildHash"], r"^[0-9a-f]{64}$")

    def test_stale_approval_and_missing_references_are_visible(self):
        song = self.song()
        stale = CONTRACT.build_catalog(
            [song], [self.band()], [self.playlist()],
            {song["songId"]: {"contentHash": "0" * 64, "approvedOn": "2026-11-06"}},
            "1.0.0-draft.1", "fixture-release",
        )
        self.assertEqual(stale["songs"][0]["approvalStatus"], "changed-since-approval")
        broken = self.band()
        broken["songIds"].append("missing-song")
        with self.assertRaisesRegex(CONTRACT.ContractError, "missing songs"):
            CONTRACT.build_catalog([song], [broken], [self.playlist()], {}, "draft", "fixture")

    def test_duplicate_json_keys_stop(self):
        with tempfile.TemporaryDirectory() as folder:
            target = Path(folder) / "duplicate.json"
            target.write_text('{"schemaVersion":1,"schemaVersion":1}')
            with self.assertRaisesRegex(CONTRACT.ContractError, "duplicate JSON key"):
                CONTRACT.load_json(target)

    def test_original_72_song_tree_is_unchanged(self):
        baseline = json.loads((ROOT / "architecture" / "baseline-5a5ff48.json").read_text())
        tree = subprocess.check_output(["git", "rev-parse", "HEAD:songs"], cwd=ROOT, text=True).strip()
        self.assertEqual(tree, baseline["gitTreeHashes"]["songs"])
        count = subprocess.check_output(["git", "ls-tree", "-r", "--name-only", "HEAD", "songs"], cwd=ROOT, text=True).splitlines()
        self.assertEqual(len(count), baseline["songCount"])


if __name__ == "__main__":
    unittest.main()
