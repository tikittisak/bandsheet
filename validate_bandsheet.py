#!/usr/bin/env python3
"""Validate the bandsheet source-of-truth layout and write an optional change report."""
import argparse
import hashlib
import json
import re
import subprocess
from collections import Counter
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SONGS = ROOT / "songs"
BANDS = ROOT / "bands"
PLAYLISTS = ROOT / "playlists"
TEMPLATE = ROOT / "_template.html"
MARKERS = ["// ── END DATA ──", "// ── END FOOTER ──", "// ── END SETTINGS ──", "// ── END SHEET META ──"]


def read(path):
    return path.read_text(encoding="utf-8")


def js_var(doc, name, marker):
    marker_pos = doc.find(marker)
    start = doc.rfind(f"var {name} = ", 0, marker_pos)
    if marker_pos < 0 or start < 0:
        raise ValueError(f"missing {name} or marker {marker}")
    raw = doc[start + len(f"var {name} = "):marker_pos].strip().rstrip(";").strip()
    return json.loads(raw)


def git_output(*args):
    try:
        return subprocess.check_output(["git", *args], cwd=ROOT, text=True, stderr=subprocess.STDOUT).strip()
    except Exception as exc:
        return f"git unavailable: {exc}"


def validate():
    errors = []
    warnings = []
    song_files = sorted(SONGS.glob("*.html"))
    song_names = {p.name for p in song_files}
    versions = Counter()
    revisions = Counter()

    template = read(TEMPLATE)
    for marker in MARKERS:
        if marker not in template:
            errors.append(f"template missing marker: {marker}")
    if re.search(r'<(?:script|link)[^>]+(?:src|href)="https?://', template):
        errors.append("template still has external script/link dependency")
    if any(token in template for token in ("Petaluma", "Roboto Mono", "font-sel", "changeChordFont")):
        errors.append("template still exposes removed font options")

    for path in song_files:
        doc = read(path)
        missing = [marker for marker in MARKERS if marker not in doc]
        if missing:
            errors.append(f"{path.relative_to(ROOT)} missing markers: {', '.join(missing)}")
        if re.search(r'<(?:script|link)[^>]+(?:src|href)="https?://', doc):
            errors.append(f"{path.relative_to(ROOT)} has external script/link dependency")
        try:
            meta = js_var(doc, "SHEET_META", "// ── END SHEET META ──")
            versions[str(meta.get("templateVersion", ""))] += 1
            revisions[str(meta.get("sheetRevision", ""))] += 1
            if meta.get("templateVersion") != "v6.18":
                errors.append(f"{path.name}: unexpected templateVersion {meta.get('templateVersion')!r}")
            if not isinstance(meta.get("sheetRevision"), int) or meta["sheetRevision"] < 1:
                errors.append(f"{path.name}: invalid sheetRevision")
            settings = js_var(doc, "SETTINGS", "// ── END SETTINGS ──")
            if settings.get("chordFont") != "Roboto Condensed":
                errors.append(f"{path.name}: unexpected chordFont")
        except (ValueError, json.JSONDecodeError) as exc:
            errors.append(f"{path.name}: invalid embedded data: {exc}")

    band_refs = []
    band_count = 0
    for path in sorted(BANDS.glob("*.json")):
        band_count += 1
        try:
            data = json.loads(read(path))
            entries = data.get("songs", [])
            if len(entries) != len(set(entries)):
                errors.append(f"{path.name}: duplicate song reference within band")
            for ref in entries:
                if not isinstance(ref, str) or ref not in song_names:
                    errors.append(f"{path.name}: missing song reference {ref!r}")
                band_refs.append(ref)
        except (json.JSONDecodeError, TypeError) as exc:
            errors.append(f"{path.name}: invalid catalog: {exc}")

    playlist_count = 0
    playlist_refs = []
    for path in sorted(PLAYLISTS.glob("*/*.json")):
        playlist_count += 1
        try:
            data = json.loads(read(path))
            page = path.with_suffix(".html")
            if not page.exists():
                errors.append(f"{path.relative_to(ROOT)} missing generated page")
            for item in data.get("songs", []):
                ref = item.get("file") if isinstance(item, dict) else item
                if ref not in song_names:
                    errors.append(f"{path.relative_to(ROOT)}: missing song reference {ref!r}")
                playlist_refs.append(ref)
        except (json.JSONDecodeError, TypeError) as exc:
            errors.append(f"{path.relative_to(ROOT)}: invalid playlist: {exc}")

    unreferenced = sorted(song_names - set(band_refs))
    if unreferenced:
        warnings.append("unreferenced songs: " + ", ".join(unreferenced))

    metrics = {
        "songs": len(song_files),
        "bands": band_count,
        "band_entries": len(band_refs),
        "unique_band_songs": len(set(band_refs)),
        "playlists": playlist_count,
        "playlist_entries": len(playlist_refs),
        "template_versions": dict(versions),
        "revisions": dict(revisions),
        "duplicate_cross_band_refs": sorted(ref for ref, count in Counter(band_refs).items() if count > 1),
        "unreferenced_songs": unreferenced,
    }
    return errors, warnings, metrics


def report_text(errors, warnings, metrics):
    status = "PASS" if not errors else "FAIL"
    lines = [f"# Bandsheet Change Report · {date.today().isoformat()}", "", f"Status: **{status}**", "", "## Inventory"]
    lines += [f"- `{key}`: `{value}`" for key, value in metrics.items()]
    lines += ["", "## Validation"]
    lines += [f"- ERROR: {item}" for item in errors] or ["- ERROR: none"]
    lines += [f"- WARNING: {item}" for item in warnings] or ["- WARNING: none"]
    lines += ["", "## Git Changes", "```text", git_output("status", "--short"), "", git_output("diff", "--stat"), "```"]
    return "\n".join(lines) + "\n"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", help="write a Markdown change report to this project-relative path")
    args = parser.parse_args()
    errors, warnings, metrics = validate()
    print(f"Bandsheet validator: {'PASS' if not errors else 'FAIL'}")
    print(json.dumps(metrics, ensure_ascii=False, indent=2))
    for item in errors:
        print(f"ERROR: {item}")
    for item in warnings:
        print(f"WARNING: {item}")
    if args.report:
        report_path = (ROOT / args.report).resolve()
        if not str(report_path).startswith(str(ROOT) + "/"):
            raise SystemExit("report must be inside the project")
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(report_text(errors, warnings, metrics), encoding="utf-8")
        print(f"Report: {report_path.relative_to(ROOT)}")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
