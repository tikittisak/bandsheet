"""Read the reviewed Luminous HTML supported by the production tools."""

from hashlib import sha256
import json
import re


# Checkpoint e8b3e96 and production commit 746eb89 identify this exact artifact.
PUBLISHED_REVIEW_SHA256 = {
    "songs/hysteria.html": "33e7f5a4075a2b9cda9c7173a6713935e40f2de23b06e3e3f22a465c65bbc759",
}
REVIEW_SLOT = re.compile(
    r'<script id="bandsheet-review-data" type="application/json">(.*?)</script>',
    re.DOTALL,
)
REVIEW_MARKER = "bandsheet-review-data"


class PublishedSheetError(ValueError):
    """The review-format sheet is outside the reviewed production scope."""


def read_song_text(path):
    with path.open(encoding="utf-8", newline="") as stream:
        doc = stream.read()
    if REVIEW_MARKER in doc:
        return doc
    # Preserve the original tools' universal-newline behavior for legacy HTML.
    return doc.replace("\r\n", "\n").replace("\r", "\n")


def read_published_review(doc, relative_path):
    if REVIEW_MARKER not in doc:
        return None
    expected = PUBLISHED_REVIEW_SHA256.get(relative_path)
    if expected is None or sha256(doc.encode("utf-8")).hexdigest() != expected:
        raise PublishedSheetError(f"{relative_path}: review HTML does not match a reviewed production artifact")
    slot = REVIEW_SLOT.search(doc)
    if slot is None:
        raise PublishedSheetError(f"{relative_path}: missing review payload")
    return json.loads(slot[1])
