#!/usr/bin/env python3
"""Block unlisted song-content drift before a bandsheet commit or push."""

import argparse
import hashlib
import html
from html.parser import HTMLParser
import json
import re
import subprocess
from datetime import date
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SONGS = ROOT / "songs"
LOCKS_PATH = ROOT / "content-locks.json"
CONTENT_FIELDS = (
    "tb-filename",
    "tb-artist",
    "meta-key",
    "meta-bpm",
    "meta-time",
    "meta-vocalist",
)


def input_value(doc, field_id):
    match = re.search(r'id="' + re.escape(field_id) + r'"[^>]*value="([^"]*)"', doc)
    return html.unescape(match.group(1)).strip() if match else ""


def json_var(doc, name, marker):
    marker_pos = doc.find(marker)
    decl = f"var {name} = "
    start = doc.rfind(decl, 0, marker_pos)
    if marker_pos < 0 or start < 0:
        raise ValueError(f"missing {name} or marker {marker}")
    raw = doc[start + len(decl):marker_pos].strip().rstrip(";").strip()
    if re.search(r"</script(?=[\s/>])", raw, re.I):
        raise ValueError(f"unsafe inline script terminator in {name}")
    return json.loads(raw)


def content_payload(doc):
    return {
        "metadata": {field: input_value(doc, field) for field in CONTENT_FIELDS},
        "sections": json_var(doc, "SECTIONS", "// ── END DATA ──"),
        "footer": json_var(doc, "FOOTER", "// ── END FOOTER ──"),
        "settings": json_var(doc, "SETTINGS", "// ── END SETTINGS ──"),
        "sheet_meta": json_var(doc, "SHEET_META", "// ── END SHEET META ──"),
    }


def content_digest(payload):
    canonical = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def load_locks():
    if not LOCKS_PATH.exists():
        return {"version": 1, "songs": {}}
    data = json.loads(LOCKS_PATH.read_text(encoding="utf-8"))
    if data.get("version") != 1 or not isinstance(data.get("songs"), dict):
        raise ValueError("content-locks.json has an unsupported format")
    return data


def lock_songs(raw_paths, note):
    paths = normalize_allowed(raw_paths)
    if not paths:
        raise ValueError("--lock requires at least one exact song path")
    if not note.strip():
        raise ValueError("--approval-note is required when locking content")
    data = load_locks()
    for rel in sorted(paths):
        path = ROOT / rel
        if not path.exists():
            raise ValueError(f"cannot lock missing song: {rel}")
        payload = content_payload(path.read_text(encoding="utf-8"))
        data["songs"][rel] = {
            "sha256": content_digest(payload),
            "approvedBy": "Ti",
            "approvedOn": date.today().isoformat(),
            "note": note.strip(),
        }
    LOCKS_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return sorted(paths)


def verify_locks():
    data = load_locks()
    errors = []
    baseline_doc = head_text("content-locks.json")
    baseline = json.loads(baseline_doc)["songs"] if baseline_doc else {}
    for rel, record in baseline.items():
        if data["songs"].get(rel) != record:
            errors.append(f"approval record removed or rewritten: {rel}; independent review required")
    for rel, record in sorted(data["songs"].items()):
        path = ROOT / rel
        if not path.exists():
            errors.append(f"locked song missing: {rel}")
            continue
        try:
            digest = content_digest(content_payload(path.read_text(encoding="utf-8")))
        except (ValueError, json.JSONDecodeError) as exc:
            errors.append(f"locked song cannot be verified: {rel}: {exc}")
            continue
        if digest != record.get("sha256"):
            errors.append(f"approved content lock mismatch: {rel}")
    return errors, len(data["songs"])


def git(*args):
    return subprocess.run(
        ["git", *args], cwd=ROOT, text=True, capture_output=True, check=False
    )


def head_text(path):
    result = git("show", f"HEAD:{path}")
    if result.returncode != 0:
        return None
    return result.stdout


def tracked_song_paths():
    result = git("ls-tree", "-r", "--name-only", "HEAD", "songs")
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "cannot read HEAD song list")
    return {line for line in result.stdout.splitlines() if line.endswith(".html")}


def worktree_song_paths():
    return {str(path.relative_to(ROOT)) for path in SONGS.glob("*.html")}


def normalize_allowed(raw_paths):
    allowed = set()
    for raw in raw_paths:
        path = Path(raw)
        if path.is_absolute():
            try:
                path = path.resolve().relative_to(ROOT)
            except ValueError as exc:
                raise ValueError(f"allowed path is outside project: {raw}") from exc
        normalized = path.as_posix()
        if not re.fullmatch(r"songs/[A-Za-z0-9][A-Za-z0-9._-]*\.html", normalized):
            raise ValueError(f"allowed path must be songs/<name>.html: {raw}")
        allowed.add(normalized)
    return allowed


def section_keys(sections):
    counts = {}
    keys = []
    for section in sections:
        label = str(section.get("label", "(unlabelled)"))
        counts[label] = counts.get(label, 0) + 1
        keys.append(f"{label} #{counts[label]}")
    return keys


def describe_change(before, after):
    if before is None:
        return "new song content"
    if after is None:
        return "song deleted"
    details = []
    metadata = [key for key in CONTENT_FIELDS if before["metadata"].get(key) != after["metadata"].get(key)]
    if metadata:
        details.append("metadata: " + ", ".join(metadata))
    before_keys = section_keys(before["sections"])
    after_keys = section_keys(after["sections"])
    if before["sections"] != after["sections"]:
        removed = [key for key in before_keys if key not in after_keys]
        added = [key for key in after_keys if key not in before_keys]
        if added:
            details.append("sections added: " + ", ".join(added))
        if removed:
            details.append("sections removed: " + ", ".join(removed))
        if not added and not removed:
            changed = []
            for key, old, new in zip(before_keys, before["sections"], after["sections"]):
                if old != new:
                    changed.append(key)
            details.append("sections changed: " + ", ".join(changed))
    if before["footer"] != after["footer"]:
        details.append("footer changed")
    if before.get("sheet_meta") != after.get("sheet_meta"):
        details.append("revision/provenance changed")
    return "; ".join(details) or "content changed"


def find_drift():
    drift = {}
    template_only = []
    for rel in sorted(tracked_song_paths() | worktree_song_paths()):
        before_doc = head_text(rel)
        work_path = ROOT / rel
        after_doc = work_path.read_text(encoding="utf-8") if work_path.exists() else None
        if before_doc == after_doc:
            continue
        try:
            before = content_payload(before_doc) if before_doc is not None else None
            after = content_payload(after_doc) if after_doc is not None else None
        except (ValueError, json.JSONDecodeError) as exc:
            drift[rel] = f"cannot verify embedded content: {exc}"
            continue
        if before == after:
            template_only.append(rel)
        else:
            drift[rel] = describe_change(before, after)
    return drift, template_only


class ExecutableHTML(HTMLParser):
    """Include unquoted handlers/URLs as browsers parse them, not just regex quotes."""
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.surfaces = []

    def handle_starttag(self, tag, attrs):
        executable = []
        for key, value in attrs:
            normalized = re.sub(r'[\x00-\x20]', '', value or '').lower()
            if key.startswith('on') or key == 'srcdoc' or normalized.startswith('javascript:'):
                executable.append((key, value))
        if tag in ('iframe', 'object', 'embed', 'base') or (tag == 'meta' and dict(attrs).get('http-equiv','').lower() == 'refresh'):
            executable = attrs
        if executable:
            self.surfaces.append((tag, executable))


def executable_payload(doc):
    """Compare executable HTML surfaces, excluding explicitly parsed data blocks."""
    for name, marker in (("SECTIONS", "DATA"), ("FOOTER", "FOOTER"),
                         ("SETTINGS", "SETTINGS"), ("SHEET_META", "SHEET META")):
        end = doc.find(f"// ── END {marker} ──")
        start = doc.rfind(f"var {name} = ", 0, end)
        if end >= 0 and start >= 0:
            doc = doc[:start] + f"var {name} = null;\n" + doc[end:]
    scripts = re.findall(r"<script\b[^>]*>[\s\S]*?</script\s*>", doc, re.I)
    parser = ExecutableHTML()
    parser.feed(doc)
    parser.close()
    return scripts, parser.surfaces


def executable_changes():
    changed = []
    for rel in sorted(tracked_song_paths()):
        before = head_text(rel)
        path = ROOT / rel
        if before is not None and path.exists():
            if executable_payload(before) != executable_payload(path.read_text(encoding="utf-8")):
                changed.append(rel)
    return changed


def main():
    parser = argparse.ArgumentParser(
        description="Fail when song metadata, sections, lyrics, chords, or footer differ from HEAD without an exact allowlist entry."
    )
    parser.add_argument(
        "--allow-code", action="append", default=[], metavar="SONG_HTML",
        help="exact explicitly reviewed executable song-code change (separate from music approval)",
    )
    parser.add_argument(
        "--allow", "--allow-content", action="append", default=[], metavar="SONG_HTML",
        help="exact intentional content-change path; repeat for multiple songs",
    )
    parser.add_argument(
        "--lock", action="append", default=[], metavar="SONG_HTML",
        help="record the current exact content hash after Ti explicitly approves it",
    )
    parser.add_argument(
        "--approval-note", default="",
        help="approval context stored with --lock",
    )
    args = parser.parse_args()
    try:
        if args.lock:
            locked = lock_songs(args.lock, args.approval_note)
            print("Content locks updated: " + ", ".join(locked))
            return 0
        allowed = normalize_allowed(args.allow)
        allowed_code = normalize_allowed(args.allow_code)
        drift, template_only = find_drift()
        lock_errors, lock_count = verify_locks()
        code_changes = set(executable_changes())
    except (RuntimeError, ValueError) as exc:
        print(f"Content guard: FAIL\nERROR: {exc}")
        return 1

    changed = set(drift)
    unapproved = changed - allowed
    unused = allowed - changed

    code_errors = (code_changes - allowed_code) | (allowed_code - code_changes)
    failed = bool(unapproved or unused or lock_errors or code_errors)
    print("Content guard: " + ("FAIL" if failed else "PASS"))
    print(f"Approved content locks verified: {lock_count}")
    for rel in template_only:
        print(f"TEMPLATE-ONLY: {rel}")
    for rel, detail in drift.items():
        status = "ALLOWED" if rel in allowed else "BLOCKED"
        print(f"{status}: {rel}: {detail}")
    for rel in sorted(unused):
        print(f"ERROR: unused allowlist entry: {rel}")
    for error in lock_errors:
        print(f"ERROR: {error}")
    for rel in sorted(code_errors):
        print(f"ERROR: executable code change requires exact review (or unused --allow-code): {rel}")
    if unapproved:
        print("ERROR: content drift requires an exact --allow-content songs/<name>.html entry")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
