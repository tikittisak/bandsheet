#!/usr/bin/env python3
"""Validate future JSON sources and derive an index catalog without reading song HTML."""

import hashlib
import html
import json
import re
from pathlib import Path


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
    return json.loads(Path(path).read_text(encoding="utf-8"), object_pairs_hook=_no_duplicate_pairs)


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


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
    required = TOP_LEVEL_KEYS - {"extensions"}
    _exact_keys(song, required, TOP_LEVEL_KEYS, "song")
    if song["schemaVersion"] != 1:
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
            if not isinstance(section.get("cols"), list):
                raise ContractError(f"sections[{index}].cols must be an array")
        elif not isinstance(section.get("bars"), list):
            raise ContractError(f"sections[{index}].bars must be an array")
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
    }


def content_hash(song):
    return sha256(canonical(semantic_payload(song)))


def revision_hash(song):
    validate_song(song)
    return sha256(canonical(song))


def _inline_json(value):
    """Serialize JSON safely inside a classic script element."""
    return canonical(value).replace("&", "\\u0026").replace("<", "\\u003c").replace(">", "\\u003e")


def _replace_block(document, name, marker, value):
    pattern = re.compile(
        rf"^var {re.escape(name)}\s*=\s*.*?;\s*\n{re.escape(marker)}$",
        re.MULTILINE | re.DOTALL,
    )
    replacement = f"var {name} = {_inline_json(value)};\n{marker}"
    document, count = pattern.subn(lambda _match: replacement, document, count=1)
    if count != 1:
        raise ContractError(f"template must contain exactly one {name} data block")
    return document


def _extract_block(document, name, marker):
    pattern = re.compile(
        rf"^var {re.escape(name)}\s*=\s*(.*?);\s*\n{re.escape(marker)}$",
        re.MULTILINE | re.DOTALL,
    )
    match = pattern.search(document)
    if not match:
        raise ContractError(f"rendered sheet is missing {name} data block")
    return json.loads(match.group(1), object_pairs_hook=_no_duplicate_pairs)


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
    document, count = re.subn(r"<title>[\s\S]*?</title>", f"<title>{title}</title>", document, count=1)
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
        "parentRevisionHash": song["provenance"]["parentRevisionHash"],
    }
    for key in ("sections", "footer", "settings"):
        name, marker = BLOCK_MARKERS[key]
        document = _replace_block(document, name, marker, song[key])
    name, marker = BLOCK_MARKERS["sheetMeta"]
    return _replace_block(document, name, marker, sheet_meta)


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
    required = {"schemaVersion", "bandId", "name", "color", "songIds"}
    _exact_keys(band, required, required, "band")
    if band["schemaVersion"] != 1 or not BAND_ID_RE.fullmatch(str(band["bandId"])):
        raise ContractError("invalid band schemaVersion or bandId")
    if not isinstance(band["songIds"], list) or len(band["songIds"]) != len(set(band["songIds"])):
        raise ContractError("band.songIds must be a unique array")
    return band


def validate_playlist(playlist):
    required = {"schemaVersion", "playlistId", "title", "bandId", "songs"}
    _exact_keys(playlist, required, required, "playlist")
    if playlist["schemaVersion"] != 1 or not isinstance(playlist["songs"], list):
        raise ContractError("invalid playlist")
    positions = []
    for item in playlist["songs"]:
        _exact_keys(item, {"position", "songId"}, {"position", "songId", "note"}, "playlist song")
        if not isinstance(item["position"], int) or item["position"] < 1:
            raise ContractError("playlist position must be an integer >= 1")
        positions.append(item["position"])
    if len(positions) != len(set(positions)):
        raise ContractError("playlist positions must be unique")
    return playlist


def build_catalog(songs, bands, playlists, approvals, index_version, release_id):
    song_map = {}
    for song in songs:
        validate_song(song)
        if song["songId"] in song_map:
            raise ContractError(f"duplicate songId: {song['songId']}")
        song_map[song["songId"]] = song

    band_ids = set()
    for band in bands:
        validate_band(band)
        if band["bandId"] in band_ids:
            raise ContractError(f"duplicate bandId: {band['bandId']}")
        band_ids.add(band["bandId"])
        missing = set(band["songIds"]) - song_map.keys()
        if missing:
            raise ContractError(f"band references missing songs: {', '.join(sorted(missing))}")

    for playlist in playlists:
        validate_playlist(playlist)
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
        elif approval.get("contentHash") == digest:
            approval_status = "approved"
        else:
            approval_status = "changed-since-approval"
        entries.append({
            "songId": song_id,
            "slug": song["slug"],
            "href": f"songs/{song['slug']}.html",
            "metadata": song["metadata"],
            "contentRevision": song["contentRevision"],
            "contentHash": digest,
            "bars": count_bars(song),
            "lyricBlocks": count_lyric_blocks(song),
            "approvalStatus": approval_status,
            "approvedOn": approval.get("approvedOn", "") if approval_status == "approved" else "",
        })

    catalog = {
        "schemaVersion": 1,
        "indexVersion": index_version,
        "releaseId": release_id,
        "songs": entries,
        "bands": sorted(bands, key=lambda item: item["bandId"]),
        "playlists": sorted(playlists, key=lambda item: item["playlistId"]),
    }
    catalog["catalogBuildHash"] = sha256(canonical(catalog))
    return catalog
