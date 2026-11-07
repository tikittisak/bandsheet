"""Read the reviewed Luminous HTML supported by the production tools."""

from functools import lru_cache
from hashlib import sha256
import json
import re
from pathlib import Path


# Checkpoint e8b3e96 and production commit 746eb89 identify this exact artifact.
PUBLISHED_REVIEW_SHA256 = {
    "songs/hysteria.html": "33e7f5a4075a2b9cda9c7173a6713935e40f2de23b06e3e3f22a465c65bbc759",
}
RC8_MANIFEST = Path(__file__).resolve().parent / "releases/luminous-v7.0.0-rc.8-review/manifest.json"
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


@lru_cache(maxsize=1)
def rc8_manifest():
    try:
        return json.loads(RC8_MANIFEST.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {}


def read_published_template(doc, relative_path):
    """Accept the blank rc.8 template at the path and hash in the release manifest."""
    if REVIEW_MARKER not in doc:
        return None
    template = rc8_manifest().get("template", {})
    if relative_path != template.get("path") or sha256(doc.encode("utf-8")).hexdigest() != template.get("sha256"):
        raise PublishedSheetError(f"{relative_path}: template does not match the rc.8 release manifest")
    slot = REVIEW_SLOT.search(doc)
    if slot is None:
        raise PublishedSheetError(f"{relative_path}: missing review payload")
    data = json.loads(slot[1])
    if "draft" not in data or "revision" in data:
        raise PublishedSheetError(f"{relative_path}: expected blank template data")
    return data


def read_published_review(doc, relative_path):
    if REVIEW_MARKER not in doc:
        return None
    digest = sha256(doc.encode("utf-8")).hexdigest()
    current = rc8_manifest().get("songs", {}).get(relative_path, {})
    if digest != current.get("sha256") and digest != PUBLISHED_REVIEW_SHA256.get(relative_path):
        raise PublishedSheetError(f"{relative_path}: review HTML does not match a reviewed production artifact")
    slot = REVIEW_SLOT.search(doc)
    if slot is None:
        raise PublishedSheetError(f"{relative_path}: missing review payload")
    return json.loads(slot[1])
