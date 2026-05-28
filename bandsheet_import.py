#!/usr/bin/env python3
import argparse
import html
import json
import os
import re
import sys
from html.parser import HTMLParser


BAND_ROOT = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_PATH = os.path.join(BAND_ROOT, "_template.html")
DEFAULT_COLOR = {"bar": "#3b82f6", "bg": "#eef4fd", "lbl": "#1e40af"}
DEFAULT_SETTINGS = {
    "chordSize": 12.5,
    "chordFont": "Lato",
    "transpose": 0,
    "noteSize": 13,
}
RHYTHM_IDS = {
    "q", "h", "dq", "dh", "e", "de", "ee", "ssss", "te",
    "rq", "re", "rs", "w", "rw", "rh", "s", "ss", "ds",
    "1q-de-s", "1q-s-de", "1q-e-s-s", "1q-s-s-e", "1q-s-e-s",
    "1q-e-re", "1q-re-e", "1q-ssss", "1q-sssr", "1q-ssrs",
    "1q-srss", "1q-rsss", "1q-ssrr", "1q-srsr", "1q-srrs",
    "1q-rssr", "1q-rsrs", "1q-rrss", "1q-srrr", "1q-rsrr",
    "1q-rrsr", "1q-rrrs", "1q-rrrr", "2q-e-de-de",
    "2q-de-de-e", "2q-de-e-de",
}
ALLOWED_NOTE_TAGS = {"p", "br", "strong", "b", "em", "i", "u"}


class NoteSanitizer(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts = []

    def handle_starttag(self, tag, attrs):
        if tag in ALLOWED_NOTE_TAGS:
            self.parts.append(f"<{tag}>")

    def handle_endtag(self, tag):
        if tag in ALLOWED_NOTE_TAGS and tag != "br":
            self.parts.append(f"</{tag}>")

    def handle_data(self, data):
        self.parts.append(html.escape(data, quote=False))


def clean_note_html(value):
    parser = NoteSanitizer()
    parser.feed(str(value or ""))
    parser.close()
    return "".join(parser.parts)


def slugify(value):
    slug = re.sub(r"[^a-zA-Z0-9\-_\s]", "", value or "").strip()
    slug = re.sub(r"\s+", "-", slug).lower()
    return slug or "bandsheet"


def ensure_template_integrity(template):
    required = [
        "// ── END DATA ──",
        "// ── END FOOTER ──",
        "// ── END SETTINGS ──",
        'id="tb-filename"',
        'id="tb-artist"',
        'id="meta-key"',
        'id="meta-bpm"',
        'id="meta-time"',
        'id="meta-vocalist"',
    ]
    missing = [item for item in required if item not in template]
    if missing:
        raise ValueError("template is missing required marker/field: " + ", ".join(missing))


def as_text(value, field, limit=180):
    if value is None:
        return ""
    if not isinstance(value, (str, int, float)):
        raise ValueError(f"{field} must be text")
    return str(value).strip()[:limit]


def validate_color(color, path):
    if color is None:
        return dict(DEFAULT_COLOR)
    if not isinstance(color, dict):
        raise ValueError(f"{path}.color must be an object")
    out = {}
    for key in ("bar", "bg", "lbl"):
        value = color.get(key, DEFAULT_COLOR[key])
        if not isinstance(value, str) or not re.fullmatch(r"#[0-9a-fA-F]{6}", value):
            raise ValueError(f"{path}.color.{key} must be #RRGGBB")
        out[key] = value
    return out


def validate_bar(bar, path):
    if not isinstance(bar, dict):
        raise ValueError(f"{path} must be an object")
    out = {
        "c": as_text(bar.get("c", "—"), f"{path}.c", 80) or "—",
        "a": as_text(bar.get("a", ""), f"{path}.a", 120),
        "h": bool(bar.get("h", False)),
    }
    for key in ("sn",):
        if key in bar:
            out[key] = as_text(bar.get(key), f"{path}.{key}", 40)
    for key in ("skipCount", "rhythmOff"):
        if key in bar:
            out[key] = bool(bar.get(key))
    if "r" in bar:
        if not isinstance(bar["r"], list):
            raise ValueError(f"{path}.r must be a list")
        rhythm = []
        for idx, note_id in enumerate(bar["r"]):
            if note_id not in RHYTHM_IDS:
                raise ValueError(f"{path}.r[{idx}] has unsupported rhythm id: {note_id}")
            rhythm.append(note_id)
        out["r"] = rhythm
    return out


def validate_section(section, index):
    path = f"sections[{index}]"
    if not isinstance(section, dict):
        raise ValueError(f"{path} must be an object")
    out = {
        "id": as_text(section.get("id", f"section-{index + 1}"), f"{path}.id", 80) or f"section-{index + 1}",
        "label": as_text(section.get("label", f"Section {index + 1}"), f"{path}.label", 80) or f"Section {index + 1}",
        "color": validate_color(section.get("color"), path),
    }
    if section.get("type") == "note":
        cols = section.get("cols", section.get("text", ["", ""]))
        if isinstance(cols, str):
            cols = [cols, ""]
        if not isinstance(cols, list):
            raise ValueError(f"{path}.cols must be a list")
        out["type"] = "note"
        out["cols"] = [clean_note_html(col) for col in cols[:2]]
        return out

    bars = section.get("bars")
    if not isinstance(bars, list) or not bars:
        raise ValueError(f"{path}.bars must be a non-empty list")
    out["note"] = as_text(section.get("note", ""), f"{path}.note", 240)
    out["noteHidden"] = bool(section.get("noteHidden", True))
    out["lyric"] = as_text(section.get("lyric", ""), f"{path}.lyric", 240)
    out["bars"] = [validate_bar(bar, f"{path}.bars[{idx}]") for idx, bar in enumerate(bars)]
    row_sizes = section.get("rowSizes", [])
    if not isinstance(row_sizes, list):
        raise ValueError(f"{path}.rowSizes must be a list")
    clean_rows = []
    for idx, size in enumerate(row_sizes):
        if not isinstance(size, int) or size < 1 or size > 8:
            raise ValueError(f"{path}.rowSizes[{idx}] must be an integer from 1 to 8")
        clean_rows.append(size)
    out["rowSizes"] = clean_rows
    if "rhythmOn" in section:
        out["rhythmOn"] = bool(section.get("rhythmOn"))
    return out


def load_payload(path):
    with open(path, encoding="utf-8") as f:
        payload = json.load(f)
    if isinstance(payload, list):
        payload = {"sections": payload}
    if not isinstance(payload, dict):
        raise ValueError("input JSON must be an object or a sections array")
    sections = payload.get("sections")
    if not isinstance(sections, list) or not sections:
        raise ValueError("input JSON must include a non-empty sections array")
    payload["sections"] = [validate_section(section, idx) for idx, section in enumerate(sections)]
    payload["title"] = as_text(payload.get("title", "New Song"), "title") or "New Song"
    payload["artist"] = as_text(payload.get("artist", ""), "artist")
    payload["key"] = as_text(payload.get("key", ""), "key", 40)
    payload["bpm"] = as_text(payload.get("bpm", ""), "bpm", 20)
    payload["time"] = as_text(payload.get("time", "4/4"), "time", 20) or "4/4"
    payload["vocalist"] = as_text(payload.get("vocalist", ""), "vocalist", 80)
    footer = payload.get("footer", {"notes": []})
    if not isinstance(footer, dict):
        raise ValueError("footer must be an object")
    notes = footer.get("notes", [])
    if not isinstance(notes, list):
        raise ValueError("footer.notes must be a list")
    payload["footer"] = {"notes": [as_text(note, "footer.notes[]", 400) for note in notes]}
    settings = dict(DEFAULT_SETTINGS)
    if isinstance(payload.get("settings"), dict):
        settings.update(payload["settings"])
    payload["settings"] = settings
    return payload


def replace_input_value(doc, field_id, value):
    safe = html.escape(value, quote=True)
    pattern = r'(id="' + re.escape(field_id) + r'"[^>]*value=")[^"]*(")'
    return re.sub(pattern, r"\g<1>" + safe + r"\g<2>", doc, count=1)


def swap_var(doc, marker, decl, payload):
    marker_index = doc.find(marker)
    if marker_index < 0:
        raise ValueError(f"missing marker: {marker}")
    decl_index = doc.rfind(decl, 0, marker_index)
    if decl_index < 0:
        raise ValueError(f"missing declaration before {marker}: {decl}")
    return doc[:decl_index] + decl + payload + ";\n" + doc[marker_index:]


def inject(template, payload):
    ensure_template_integrity(template)
    title = payload["title"]
    artist = payload["artist"]
    doc = re.sub(
        r"<title>[^<]*</title>",
        "<title>" + html.escape(title, quote=False) + " · bandsheet</title>",
        template,
        count=1,
    )
    doc = replace_input_value(doc, "tb-filename", title)
    doc = replace_input_value(doc, "tb-artist", f"— {artist}" if artist else "")
    doc = replace_input_value(doc, "meta-key", payload["key"])
    doc = replace_input_value(doc, "meta-bpm", payload["bpm"])
    doc = replace_input_value(doc, "meta-time", payload["time"])
    doc = replace_input_value(doc, "meta-vocalist", payload["vocalist"])
    doc = swap_var(doc, "// ── END DATA ──", "var SECTIONS = ", json.dumps(payload["sections"], ensure_ascii=False))
    doc = swap_var(doc, "// ── END FOOTER ──", "var FOOTER = ", json.dumps(payload["footer"], ensure_ascii=False))
    doc = swap_var(doc, "// ── END SETTINGS ──", "var SETTINGS = ", json.dumps(payload["settings"], ensure_ascii=False))
    return "<!DOCTYPE html>\n" + doc


def main():
    parser = argparse.ArgumentParser(description="Validate AI-generated bandsheet JSON and inject it into _template.html.")
    parser.add_argument("input_json", help="JSON file containing title, metadata, and sections")
    parser.add_argument("--check", action="store_true", help="Validate the JSON and template without writing HTML")
    parser.add_argument("--band", default="", help="Band folder for default output path")
    parser.add_argument("--output", default="", help="Output HTML path")
    args = parser.parse_args()

    try:
        payload = load_payload(args.input_json)
        with open(TEMPLATE_PATH, encoding="utf-8") as f:
            template = f.read()
        ensure_template_integrity(template)
        if args.check:
            print(f"OK valid input: {len(payload['sections'])} sections")
            return 0
        out = args.output
        if not out:
            if not args.band:
                raise ValueError("provide --band or --output")
            out = os.path.join(BAND_ROOT, args.band, slugify(payload["title"]) + ".html")
        out = os.path.abspath(out)
        if not out.startswith(BAND_ROOT + os.sep):
            raise ValueError("output must be inside the bandsheet project")
        os.makedirs(os.path.dirname(out), exist_ok=True)
        with open(out, "w", encoding="utf-8") as f:
            f.write(inject(template, payload))
        print(f"OK wrote {os.path.relpath(out, BAND_ROOT)}")
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
