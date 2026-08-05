#!/usr/bin/env python3
import argparse
import html
import importlib.util
import json
import os
import re
import sys
from pathlib import Path


BAND_ROOT = Path(__file__).resolve().parent
TEMPLATE_PATH = BAND_ROOT / "_template.html"


def read_text(path):
    return Path(path).read_text(encoding="utf-8")


def input_value(doc, field_id):
    match = re.search(r'id="' + re.escape(field_id) + r'"[^>]*value="([^"]*)"', doc)
    return html.unescape(match.group(1)).strip() if match else ""


def extract_json_var(doc, name, marker):
    marker_index = doc.find(marker)
    if marker_index < 0:
        raise ValueError(f"missing marker: {marker}")
    decl = f"var {name} = "
    decl_index = doc.rfind(decl, 0, marker_index)
    if decl_index < 0:
        raise ValueError(f"missing declaration before {marker}: {decl}")
    payload = doc[decl_index + len(decl):marker_index].strip()
    if payload.endswith(";"):
        payload = payload[:-1].strip()
    return json.loads(payload)


def load_bandsheet_import():
    path = BAND_ROOT / "bandsheet_import.py"
    spec = importlib.util.spec_from_file_location("bandsheet_import", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def normalize_artist(value):
    artist = (value or "").strip()
    for prefix in ("—", "-"):
        if artist.startswith(prefix):
            return artist[len(prefix):].strip()
    return artist


def slugify(value):
    slug = re.sub(r"[^a-zA-Z0-9\-_\s]", "", value or "").strip()
    slug = re.sub(r"\s+", "-", slug).lower()
    return slug or "bandsheet"


def infer_output(payload, source_path):
    source_name = Path(source_path).stem
    source_slug = slugify(re.sub(r"\s*\(\d+\)$", "", source_name))
    title_slug = slugify(payload.get("title", ""))
    candidates = []
    for slug in (source_slug, title_slug):
        if slug:
            candidates.append(BAND_ROOT / "songs" / f"{slug}.html")
    for candidate in candidates:
        if candidate.exists():
            return candidate
    if title_slug:
        return BAND_ROOT / "songs" / f"{title_slug}.html"
    raise ValueError("cannot infer output path; pass --output")


def extract_payload(source_html):
    doc = read_text(source_html)
    title = input_value(doc, "tb-filename")
    artist = normalize_artist(input_value(doc, "tb-artist"))
    payload = {
        "title": title,
        "artist": artist,
        "key": input_value(doc, "meta-key"),
        "bpm": input_value(doc, "meta-bpm"),
        "time": input_value(doc, "meta-time") or "4/4",
        "vocalist": input_value(doc, "meta-vocalist"),
        "sections": extract_json_var(doc, "SECTIONS", "// ── END DATA ──"),
        "footer": extract_json_var(doc, "FOOTER", "// ── END FOOTER ──"),
        "settings": extract_json_var(doc, "SETTINGS", "// ── END SETTINGS ──"),
    }
    if not payload["title"]:
        raise ValueError("missing song title in tb-filename")
    if not isinstance(payload["sections"], list) or not payload["sections"]:
        raise ValueError("SECTIONS must be a non-empty list")
    if not isinstance(payload["footer"], dict):
        raise ValueError("FOOTER must be an object")
    if not isinstance(payload["settings"], dict):
        raise ValueError("SETTINGS must be an object")
    return payload


def count_bars(sections):
    return sum(
        1
        for section in sections
        if isinstance(section, dict) and section.get("type") != "note"
        for bar in section.get("bars", [])
        if not (isinstance(bar, dict) and bar.get("skipCount"))
    )


def ensure_clean_output(doc):
    if '<div id="sheet" style=' in doc:
        raise ValueError("generated output contains rendered #sheet DOM")
    if "body.edit-mode.view-mini .bar-cell{justify-content:flex-start" in doc:
        raise ValueError("generated output contains stale edit-mini chord layout")
    if re.match(r"\s*<!DOCTYPE html>\s*<!DOCTYPE html>", doc, re.IGNORECASE):
        raise ValueError("generated output contains duplicate doctype")


def main():
    parser = argparse.ArgumentParser(
        description="Import a browser-saved edited bandsheet HTML by extracting data and regenerating from _template.html."
    )
    parser.add_argument("source_html", help="Edited/downloaded song HTML")
    parser.add_argument("--output", help="Output song HTML path. Defaults to matching songs/{slug}.html")
    parser.add_argument("--check", action="store_true", help="Validate and preview without writing")
    args = parser.parse_args()

    try:
        source = Path(args.source_html).expanduser().resolve()
        payload = extract_payload(source)
        output = Path(args.output).expanduser().resolve() if args.output else infer_output(payload, source)
        if not str(output).startswith(str(BAND_ROOT) + os.sep):
            raise ValueError("output must be inside the bandsheet project")

        importer = load_bandsheet_import()
        template = read_text(TEMPLATE_PATH)
        generated = importer.inject(template, payload)
        ensure_clean_output(generated)

        section_count = len(payload["sections"])
        bar_count = count_bars(payload["sections"])
        if args.check:
            print(f"OK check: {payload['title']} -> {output.relative_to(BAND_ROOT)}")
            print(f"sections: {section_count}, bars: {bar_count}")
            return 0

        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(generated, encoding="utf-8")
        print(f"OK wrote {output.relative_to(BAND_ROOT)}")
        print(f"sections: {section_count}, bars: {bar_count}")
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
