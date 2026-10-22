#!/usr/bin/env python3
"""Preflight a playlist for completeness and Ti-approved content locks."""

import argparse
import importlib.util
import json
from datetime import date
from pathlib import Path


ROOT = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("content_guard", ROOT / "content_guard.py")
guard = importlib.util.module_from_spec(spec)
spec.loader.exec_module(guard)


def js_var(doc, name, marker):
    marker_pos = doc.find(marker)
    decl = f"var {name} = "
    start = doc.rfind(decl, 0, marker_pos)
    if marker_pos < 0 or start < 0:
        raise ValueError(f"missing {name}")
    return json.loads(doc[start + len(decl):marker_pos].strip().rstrip(";").strip())


def inspect_song(rel, locks, lyrics_optional=False):
    path = ROOT / rel
    doc = path.read_text(encoding="utf-8")
    payload = guard.content_payload(doc)
    sections = payload["sections"]
    meta = js_var(doc, "SHEET_META", "// ── END SHEET META ──")
    bars = sum(len(section.get("bars", [])) for section in sections)
    lyric_blocks = sum(1 for section in sections if section.get("type") == "note" and any(str(col).strip() for col in section.get("cols", [])))
    locked = locks.get(rel, {}).get("sha256") == guard.content_digest(payload)
    issues = []
    if bars <= 4 or meta.get("contentSource") == "blank-baseline":
        issues.append("incomplete/blank arrangement")
    if meta.get("contentSource") == "migration-baseline" and not locked:
        issues.append("provenance gap: migration baseline never Ti-approved")
    if bars > 4 and lyric_blocks == 0 and not lyrics_optional:
        issues.append("no lyric blocks")
    if not locked:
        issues.append("not Ti-approved/locked")
    return {
        "bars": bars,
        "lyricBlocks": lyric_blocks,
        "revision": meta.get("sheetRevision", ""),
        "source": meta.get("contentSource", ""),
        "locked": locked,
        "issues": issues,
    }


def report(title, rows):
    ready = sum(1 for row in rows if not row["audit"]["issues"])
    lines = [
        f"# Rehearsal Readiness · {title}",
        "",
        f"Date: `{date.today().isoformat()}`",
        f"Ready: **{ready}/{len(rows)}**",
        "",
        "| Set | Song file | Bars | Lyrics | Rev | Lock | Issues |",
        "|---:|---|---:|---:|---:|---|---|",
    ]
    for row in rows:
        audit = row["audit"]
        lines.append(
            f"| {row['setlist']} | `{row['file']}` | {audit['bars']} | {audit['lyricBlocks']} | "
            f"{audit['revision']} | {'approved' if audit['locked'] else 'unlocked'} | "
            f"{'; '.join(audit['issues']) or '—'} |"
        )
    return "\n".join(lines) + "\n"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("playlist", help="project-relative playlist JSON")
    parser.add_argument("--report", help="project-relative Markdown output")
    args = parser.parse_args()

    playlist_path = (ROOT / args.playlist).resolve()
    if not str(playlist_path).startswith(str(ROOT) + "/") or not playlist_path.exists():
        raise SystemExit("playlist must exist inside the project")
    playlist = json.loads(playlist_path.read_text(encoding="utf-8"))
    locks = guard.load_locks()["songs"]
    rows = []
    for item in playlist.get("songs", []):
        rel = "songs/" + item["file"]
        rows.append({
            "setlist": item.get("setlist", ""),
            "file": item["file"],
            "audit": inspect_song(rel, locks, bool(item.get("lyricsOptional"))),
        })

    output = report(playlist.get("title", playlist_path.stem), rows)
    print(output, end="")
    if args.report:
        report_path = (ROOT / args.report).resolve()
        if not str(report_path).startswith(str(ROOT) + "/"):
            raise SystemExit("report must be inside the project")
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(output, encoding="utf-8")
        print(f"Report: {report_path.relative_to(ROOT)}")
    return 1 if any(row["audit"]["issues"] for row in rows) else 0


if __name__ == "__main__":
    raise SystemExit(main())
