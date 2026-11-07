#!/usr/bin/env python3
"""Validate future JSON sources and derive an index catalog without reading song HTML."""

import hashlib
import html
import json
import re
import math
import struct
import importlib.util
from datetime import date
from pathlib import Path

_schema_spec = importlib.util.spec_from_file_location('bandsheet_schema_check', Path(__file__).with_name('schema_check.py'))
_schema_check = importlib.util.module_from_spec(_schema_spec)
_schema_spec.loader.exec_module(_schema_check)


def validate_schema(value, name):
    schema = json.loads((Path(__file__).resolve().parents[1] / 'schemas' / (name+'.schema.json')).read_text())
    try:
        canonical(value)
        return _schema_check.validate(value, schema)
    except ValueError as exc:
        raise ContractError(str(exc)) from exc


SONG_ID_RE = re.compile(r"^[a-z0-9][a-z0-9._-]{2,63}$")
SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9-]{1,79}$")
BAND_ID_RE = re.compile(r"^[a-z0-9][a-z0-9-]{1,63}$")
TOP_LEVEL_KEYS = {
    "schemaVersion",
    "songId",
    "slug",
    "contentRevision",
    "provenance",
    "metadata",
    "sections",
    "footer",
    "settings",
    "extensions",
}
METADATA_KEYS = {"title", "artist", "key", "bpm", "timeSignature", "vocalist"}
PROVENANCE_KEYS = {"sourceType", "capturedOn", "parentRevisionHash", "sourceRef", "note"}


class ContractError(ValueError):
    pass


BLOCK_MARKERS = {
    "sections": ("SECTIONS", "// ── END DATA ──"),
    "footer": ("FOOTER", "// ── END FOOTER ──"),
    "settings": ("SETTINGS", "// ── END SETTINGS ──"),
    "sheetMeta": ("SHEET_META", "// ── END SHEET META ──"),
}
INPUT_IDS = {
    "title": "tb-filename",
    "artist": "tb-artist",
    "key": "meta-key",
    "bpm": "meta-bpm",
    "timeSignature": "meta-time",
    "vocalist": "meta-vocalist",
}


def _no_duplicate_pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ContractError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def load_json(path):
    return parse_json(Path(path).read_text(encoding="utf-8"))


def parse_json(raw):
    def invalid(value):
        raise ContractError(f"non-finite JSON number: {value}")
    value = json.loads(raw, object_pairs_hook=_no_duplicate_pairs, parse_constant=invalid)
    canonical(value)  # Also reject invalid Unicode / numbers outside the portable domain.
    return value


def canonical(value):
    """bandsheet-c14n-1: type-tagged JSON; numbers are big-endian binary64 hex.

    This is a fingerprint encoding, NOT a song document serializer. UTF-8 key
    order, finite binary64, safe integers, and normalized signed zero are shared
    with src/sheet/revision-client.js. No text normalization is performed.
    """
    def tagged(v):
        if v is None:
            return ["null"]
        if isinstance(v, bool):
            return ["boolean", v]
        if isinstance(v, str):
            try:
                v.encode("utf-8")
            except UnicodeEncodeError as exc:
                raise ContractError("unpaired Unicode surrogate") from exc
            return ["string", v]
        if isinstance(v, (int, float)):
            if (isinstance(v, int) and abs(v) > 9007199254740991) or not math.isfinite(v) or (v == int(v) and abs(v) > 9007199254740991):
                raise ContractError("number outside portable JSON domain")
            return ["number", struct.pack(">d", 0.0 if v == 0 else float(v)).hex()]
        if isinstance(v, list):
            return ["array", [tagged(x) for x in v]]
        if isinstance(v, dict):
            for key in v:
                if not isinstance(key, str):
                    raise ContractError("JSON object keys must be strings")
                tagged(key)
            return ["object", [[key, tagged(v[key])] for key in sorted(v, key=lambda k: k.encode("utf-8"))]]
        raise ContractError("not a JSON value")
    return json.dumps(tagged(value), ensure_ascii=False, separators=(",", ":"), allow_nan=False)


def document_json(value):
    canonical(value)
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


def sha256(value):
    raw = value if isinstance(value, bytes) else value.encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _exact_keys(value, required, allowed, label):
    if not isinstance(value, dict):
        raise ContractError(f"{label} must be an object")
    missing = required - value.keys()
    unknown = value.keys() - allowed
    if missing:
        raise ContractError(f"{label} missing keys: {', '.join(sorted(missing))}")
    if unknown:
        raise ContractError(f"{label} unknown keys: {', '.join(sorted(unknown))}")


def validate_song(song):
    validate_schema(song, 'song')
    required = TOP_LEVEL_KEYS - {"extensions"}
    _exact_keys(song, required, TOP_LEVEL_KEYS, "song")
    if type(song["schemaVersion"]) is not int or song["schemaVersion"] != 1:
        raise ContractError("unsupported song schemaVersion")
    if not isinstance(song["songId"], str) or not SONG_ID_RE.fullmatch(song["songId"]):
        raise ContractError("invalid songId")
    if not isinstance(song["slug"], str) or not SLUG_RE.fullmatch(song["slug"]):
        raise ContractError("invalid slug")
    if not isinstance(song["contentRevision"], int) or isinstance(song["contentRevision"], bool) or song["contentRevision"] < 1:
        raise ContractError("contentRevision must be an integer >= 1")

    provenance_required = {"sourceType", "capturedOn", "parentRevisionHash"}
    _exact_keys(song["provenance"], provenance_required, PROVENANCE_KEYS, "provenance")
    if not isinstance(song["provenance"]["sourceType"], str) or not song["provenance"]["sourceType"].strip():
        raise ContractError("provenance.sourceType is required")
    if not isinstance(song["provenance"]["capturedOn"], str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", song["provenance"]["capturedOn"]):
        raise ContractError("provenance.capturedOn must be YYYY-MM-DD")
    try:
        date.fromisoformat(song["provenance"]["capturedOn"])
    except ValueError as exc:
        raise ContractError("invalid capturedOn date") from exc
    for key in ("sourceRef", "note"):
        if key in song["provenance"] and not isinstance(song["provenance"][key], str):
            raise ContractError(f"provenance.{key} must be a string")
    parent = song["provenance"]["parentRevisionHash"]
    if parent is not None and (not isinstance(parent, str) or not re.fullmatch(r"[0-9a-f]{64}", parent)):
        raise ContractError("parentRevisionHash must be null or SHA-256")

    _exact_keys(song["metadata"], METADATA_KEYS, METADATA_KEYS, "metadata")
    for key, value in song["metadata"].items():
        if not isinstance(value, str):
            raise ContractError(f"metadata.{key} must be a string")
    if not song["metadata"]["title"].strip():
        raise ContractError("metadata.title is required")

    if not isinstance(song["sections"], list):
        raise ContractError("sections must be an array")
    for index, section in enumerate(song["sections"]):
        if not isinstance(section, dict):
            raise ContractError(f"sections[{index}] must be an object")
        if section.get("type") == "note":
            if not isinstance(section.get("cols"), list) or any(not isinstance(x, str) for x in section["cols"]):
                raise ContractError(f"sections[{index}].cols must be an array")
        elif not isinstance(section.get("bars"), list):
            raise ContractError(f"sections[{index}].bars must be an array")
        else:
            for bar in section["bars"]:
                if not isinstance(bar, dict) or not isinstance(bar.get("c"), str):
                    raise ContractError("each chord bar must be an object with string c")
        if "rowSizes" in section and (not isinstance(section["rowSizes"], list) or any(type(n) is not int or not 1 <= n <= 8 for n in section["rowSizes"])):
            raise ContractError("rowSizes must contain integers 1..8")
    if not isinstance(song["footer"], dict) or not isinstance(song["settings"], dict):
        raise ContractError("footer and settings must be objects")
    if "extensions" in song and not isinstance(song["extensions"], dict):
        raise ContractError("extensions must be an object")
    return song


def semantic_payload(song):
    validate_song(song)
    return {
        "metadata": song["metadata"],
        "sections": song["sections"],
        "footer": song["footer"],
        "settings": song["settings"],
        "extensions": song.get("extensions", {}),
    }


def content_hash(song):
    return sha256(canonical(semantic_payload(song)))


def revision_hash(song):
    validate_song(song)
    return sha256(canonical(song))


def _inline_json(value):
    """Serialize JSON safely inside a classic script element."""
    return document_json(value).replace("&", "\\u0026").replace("<", "\\u003c").replace(">", "\\u003e")


def _replace_block(document, name, marker, value):
    pattern = re.compile(
        rf"^var {re.escape(name)}\s*=\s*.*?;\s*\n{re.escape(marker)}$",
        re.MULTILINE | re.DOTALL,
    )
    replacement = f"var {name} = {_inline_json(value)};\n{marker}"
    if len(list(pattern.finditer(document))) != 1:
        raise ContractError(f"template must contain exactly one {name} data block")
    document, count = pattern.subn(lambda _match: replacement, document)
    return document


def _extract_block(document, name, marker):
    pattern = re.compile(
        rf"^var {re.escape(name)}\s*=\s*(.*?);\s*\n{re.escape(marker)}$",
        re.MULTILINE | re.DOTALL,
    )
    match = pattern.search(document)
    if not match:
        raise ContractError(f"rendered sheet is missing {name} data block")
    return parse_json(match.group(1))


def _replace_input_value(document, element_id, value):
    pattern = re.compile(rf'(<input\b[^>]*\bid="{re.escape(element_id)}"[^>]*\bvalue=")[^"]*(")')
    replacement = html.escape(value, quote=True)
    document, count = pattern.subn(lambda match: match.group(1) + replacement + match.group(2), document, count=1)
    if count != 1:
        raise ContractError(f"template is missing input #{element_id}")
    return document


def _extract_input_value(document, element_id):
    pattern = re.compile(rf'<input\b[^>]*\bid="{re.escape(element_id)}"[^>]*\bvalue="([^"]*)"')
    match = pattern.search(document)
    if not match:
        raise ContractError(f"rendered sheet is missing input #{element_id}")
    return html.unescape(match.group(1))


def render_song_html(template, song, editor_version):
    """Render a self-contained review sheet without changing the song revision."""
    validate_song(song)
    document = template
    for metadata_key, element_id in INPUT_IDS.items():
        document = _replace_input_value(document, element_id, song["metadata"][metadata_key])
    title = html.escape(f"{song['metadata']['title']} · Bandsheet")
    document, count = re.subn(r"<title>[\s\S]*?</title>", lambda _: f"<title>{title}</title>", document, count=1)
    if count != 1:
        raise ContractError("template is missing title")

    sheet_meta = {
        "templateVersion": "v6.19",
        "uiVersion": editor_version,
        "dataSchemaVersion": song["schemaVersion"],
        "songId": song["songId"],
        "sheetRevision": song["contentRevision"],
        "contentRevision": song["contentRevision"],
        "contentUpdated": song["provenance"]["capturedOn"],
        "contentSource": song["provenance"]["sourceType"],
        "contentHash": content_hash(song),
        "revisionHash": revision_hash(song),
        "parentRevisionHash": song["provenance"]["parentRevisionHash"],
    }
    for key in ("sections", "footer", "settings"):
        name, marker = BLOCK_MARKERS[key]
        document = _replace_block(document, name, marker, song[key])
    name, marker = BLOCK_MARKERS["sheetMeta"]
    document = _replace_block(document, name, marker, sheet_meta)
    # Only a derived synthetic adapter is changed; the frozen template is never written.
    document = document.replace("SETTINGS.chordFont=CHORD_FONT;", "// Display defaults must not mutate SETTINGS.")
    document = document.replace("      if(!sec.rowSizes)sec.rowSizes=[];\n      var pos=", "      var pos=")
    document = document.replace("sec.rowSizes[ri]||DEFAULT_ROW_SIZE", "(sec.rowSizes||[])[ri]||DEFAULT_ROW_SIZE")
    # Fail closed if the revision adapter fails to initialize: never fall back to
    # the retired download-as-Save implementation in this derived page.
    for start, end, replacement in (
        ("function saveToFile(){", "\nfunction updateTitle(){", "function saveToFile(){throw new Error('Revision client unavailable; Save blocked')}\n"),
        ("function downloadTemplate(){", "\nfunction auditEscape(", "function downloadTemplate(){throw new Error('Legacy template export is retired in the synthetic lab')}\n"),
    ):
        if document.count(start) != 1 or document.count(end) != 1:
            raise ContractError("unsupported synthetic adapter boundary")
        left = document.index(start)
        right = document.index(end, left)
        document = document[:left] + replacement + document[right:]
    envelope = '<script id="bandsheet-revision" type="application/json">' + _inline_json(song) + '</script>'
    client = (Path(__file__).resolve().parents[1] / "src/sheet/revision-client.js").read_text(encoding="utf-8")
    return document.replace("</body>", envelope + "<script>" + client + "</script></body>")


def extract_rendered_payload(document):
    """Reopen the embedded semantic payload for deterministic round-trip checks."""
    metadata = {
        metadata_key: _extract_input_value(document, element_id)
        for metadata_key, element_id in INPUT_IDS.items()
    }
    payload = {"metadata": metadata}
    for key in ("sections", "footer", "settings"):
        name, marker = BLOCK_MARKERS[key]
        payload[key] = _extract_block(document, name, marker)
    name, marker = BLOCK_MARKERS["sheetMeta"]
    payload["sheetMeta"] = _extract_block(document, name, marker)
    match = re.search(r'<script id="bandsheet-revision" type="application/json">(.*?)</script>', document, re.S)
    if not match:
        raise ContractError("missing full revision envelope")
    revision = parse_json(match.group(1))
    validate_song(revision)
    payload["revision"] = revision
    payload["extensions"] = revision.get("extensions", {})
    return payload


def count_bars(song):
    return sum(
        1
        for section in song["sections"]
        for bar in section.get("bars", [])
        if not (isinstance(bar, dict) and bar.get("skipCount"))
    )


def count_lyric_blocks(song):
    return sum(
        1
        for section in song["sections"]
        if section.get("type") == "note" and any(str(col).strip() for col in section.get("cols", []))
    )


def validate_band(band):
    validate_schema(band, 'band')
    required = {"schemaVersion", "bandId", "name", "color", "songIds"}
    _exact_keys(band, required, required, "band")
    if type(band["schemaVersion"]) is not int or band["schemaVersion"] != 1 or not isinstance(band["bandId"], str) or not BAND_ID_RE.fullmatch(band["bandId"]):
        raise ContractError("invalid band schemaVersion or bandId")
    if not isinstance(band["name"], str) or not band["name"].strip() or not isinstance(band["color"], str) or not re.fullmatch(r"#[0-9a-fA-F]{6}", band["color"]):
        raise ContractError("invalid band name/color")
    if not isinstance(band["songIds"], list) or any(not isinstance(x, str) or not SONG_ID_RE.fullmatch(x) for x in band["songIds"]) or len(band["songIds"]) != len(set(band["songIds"])):
        raise ContractError("band.songIds must be a unique array")
    return band


def validate_playlist(playlist):
    validate_schema(playlist, 'playlist')
    required = {"schemaVersion", "playlistId", "title", "bandId", "songs"}
    _exact_keys(playlist, required, required, "playlist")
    if type(playlist["schemaVersion"]) is not int or playlist["schemaVersion"] != 1 or not isinstance(playlist["songs"], list):
        raise ContractError("invalid playlist")
    if not isinstance(playlist["playlistId"], str) or not SLUG_RE.fullmatch(playlist["playlistId"]) or not isinstance(playlist["title"], str) or not playlist["title"].strip() or not isinstance(playlist["bandId"], str) or not BAND_ID_RE.fullmatch(playlist["bandId"]):
        raise ContractError("invalid playlist identity/title")
    positions = []
    for item in playlist["songs"]:
        _exact_keys(item, {"position", "songId"}, {"position", "songId", "note"}, "playlist song")
        if type(item["position"]) is not int or item["position"] < 1:
            raise ContractError("playlist position must be an integer >= 1")
        if not isinstance(item["songId"], str) or not SONG_ID_RE.fullmatch(item["songId"]) or ("note" in item and not isinstance(item["note"], str)):
            raise ContractError("invalid playlist song reference/note")
        positions.append(item["position"])
    if len(positions) != len(set(positions)):
        raise ContractError("playlist positions must be unique")
    return playlist


def build_catalog(songs, bands, playlists, approvals, index_version, release_id):
    song_map = {}
    slugs = set()
    for song in songs:
        validate_song(song)
        if song["songId"] in song_map:
            raise ContractError(f"duplicate songId: {song['songId']}")
        song_map[song["songId"]] = song
        if song["slug"] in slugs:
            raise ContractError("duplicate song slug")
        slugs.add(song["slug"])

    band_ids = set()
    for band in bands:
        validate_band(band)
        if band["bandId"] in band_ids:
            raise ContractError(f"duplicate bandId: {band['bandId']}")
        band_ids.add(band["bandId"])
        missing = set(band["songIds"]) - song_map.keys()
        if missing:
            raise ContractError(f"band references missing songs: {', '.join(sorted(missing))}")

    playlist_ids = set()
    for playlist in playlists:
        validate_playlist(playlist)
        if playlist["playlistId"] in playlist_ids:
            raise ContractError("duplicate playlistId")
        playlist_ids.add(playlist["playlistId"])
        if playlist["bandId"] not in band_ids:
            raise ContractError(f"playlist references missing band: {playlist['bandId']}")
        missing = {item["songId"] for item in playlist["songs"]} - song_map.keys()
        if missing:
            raise ContractError(f"playlist references missing songs: {', '.join(sorted(missing))}")

    entries = []
    for song_id in sorted(song_map):
        song = song_map[song_id]
        digest = content_hash(song)
        approval = approvals.get(song_id)
        if approval is None:
            approval_status = "unapproved"
        elif approval.get("contentHash") == digest and approval.get("revisionHash") == revision_hash(song) and approval.get("songId") == song_id:
            # A local record is a claim, not proof of Ti's authority.
            approval_status = "approval-record-present-unverified"
        else:
            approval_status = "changed-since-approval"
        entries.append({
            "songId": song_id,
            "slug": song["slug"],
            "href": f"songs/{song['slug']}.html",
            "metadata": song["metadata"],
            "contentRevision": song["contentRevision"],
            "contentHash": digest,
            "revisionHash": revision_hash(song),
            "bars": count_bars(song),
            "lyricBlocks": count_lyric_blocks(song),
            "approvalStatus": approval_status,
            "approvedOn": approval.get("approvedOn", "") if approval_status == "approved" else "",
        })

    catalog = {
        "schemaVersion": 1,
        "songs": entries,
        "bands": sorted(bands, key=lambda item: item["bandId"]),
        "playlists": sorted(playlists, key=lambda item: item["playlistId"]),
    }
    catalog["catalogBuildHash"] = sha256(canonical(catalog))
    validate_schema(catalog, 'catalog')
    return parse_json(document_json(catalog))  # No mutable aliases to input revisions.
