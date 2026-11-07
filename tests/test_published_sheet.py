from contextlib import redirect_stdout
from io import StringIO
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import content_guard
from published_sheet import PublishedSheetError, read_published_review, read_song_text
import update_index

ROOT = Path(__file__).resolve().parents[1]
HYSTERIA = "songs/hysteria.html"


class PublishedSheetTests(unittest.TestCase):
    def test_index_reads_released_hysteria(self):
        self.assertEqual(update_index.extract_meta(ROOT / HYSTERIA), {
            "title": "Hysteria", "artist": "Muse", "key": "A minor", "bpm": "93",
            "vocalist": "TI", "bars": "88", "file": "hysteria.html",
        })

    def test_review_file_is_bound_to_path_and_bytes(self):
        doc = read_song_text(ROOT / HYSTERIA)
        self.assertEqual(read_published_review(doc, HYSTERIA)["revision"]["contentRevision"], 4)
        for changed, path in (
            (doc, "songs/another-song.html"),
            (doc.replace("\n", "\r\n"), HYSTERIA),
            (doc.replace('"bpm":"93"', '"bpm":"94"', 1), HYSTERIA),
        ):
            with self.subTest(path=path, changed=changed != doc):
                with self.assertRaises(PublishedSheetError):
                    read_published_review(changed, path)

    def test_content_allowlist_cannot_admit_modified_review_html(self):
        doc = read_song_text(ROOT / HYSTERIA)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            song = root / HYSTERIA
            song.parent.mkdir()
            song.write_text(doc + "\n", encoding="utf-8")
            locks = root / "content-locks.json"
            locks.write_text(json.dumps({"version": 1, "songs": {}}), encoding="utf-8")
            output = StringIO()
            baseline = {HYSTERIA: doc, "content-locks.json": locks.read_text(encoding="utf-8")}
            with patch.multiple(content_guard, ROOT=root, SONGS=song.parent, LOCKS_PATH=locks), \
                 patch.object(content_guard, "head_text", side_effect=baseline.get), \
                 patch.object(content_guard, "tracked_song_paths", return_value={HYSTERIA}), \
                 patch("sys.argv", ["content_guard.py", "--allow-content", HYSTERIA]), \
                 redirect_stdout(output):
                self.assertEqual(content_guard.main(), 1)
            self.assertIn("review HTML does not match a reviewed production artifact", output.getvalue())


if __name__ == "__main__":
    unittest.main()
