#!/usr/bin/env python3
import argparse
import html
import json
import os
import re
import sys
import tempfile
import urllib.request
from html.parser import HTMLParser

import bandsheet_import


BAND_ROOT = os.path.dirname(os.path.abspath(__file__))

COLORS = {
    "intro": {"bar": "#ff3b30", "bg": "#fff1f0", "lbl": "#b00008"},
    "outro": {"bar": "#ff3b30", "bg": "#fff1f0", "lbl": "#b00008"},
    "verse": {"bar": "#3b82f6", "bg": "#eef4fd", "lbl": "#1e40af"},
    "pre": {"bar": "#f59e0b", "bg": "#fffbeb", "lbl": "#78350f"},
    "chorus": {"bar": "#ffcc00", "bg": "#fffbe6", "lbl": "#7a5e00"},
    "bridge": {"bar": "#059669", "bg": "#eafaf4", "lbl": "#064e3b"},
    "instrument": {"bar": "#8b5cf6", "bg": "#f5f3ff", "lbl": "#4c1d95"},
    "groove": {"bar": "#ff6b30", "bg": "#fff3ed", "lbl": "#8a2e00"},
}


class TextExtractor(HTMLParser):
    BLOCK_TAGS = {"h1", "h2", "h3", "h4", "p", "div", "section", "article", "br", "li", "tr"}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts = []
        self.skip = 0

    def handle_starttag(self, tag, attrs):
        if tag in {"script", "style", "svg"}:
            self.skip += 1
        elif tag in self.BLOCK_TAGS:
            self.parts.append("\n")

    def handle_endtag(self, tag):
        if tag in {"script", "style", "svg"} and self.skip:
            self.skip -= 1
        elif tag in self.BLOCK_TAGS:
            self.parts.append("\n")

    def handle_data(self, data):
        if not self.skip:
            self.parts.append(data)


def html_to_text(doc):
    parser = TextExtractor()
    parser.feed(doc)
    parser.close()
    text = html.unescape("".join(parser.parts))
    text = re.sub(r"[ \t\xa0]+", " ", text)
    text = re.sub(r"\n\s*\n\s*\n+", "\n\n", text)
    return text.strip()


def slugify(value):
    return bandsheet_import.slugify(value)


def read_source(source):
    if not source or source == "-":
        return sys.stdin.read()
    if re.match(r"https?://", source):
        req = urllib.request.Request(source, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=20) as res:
            raw = res.read().decode("utf-8", "replace")
        return html_to_text(raw) if "<html" in raw[:1000].lower() else raw
    with open(source, encoding="utf-8") as f:
        raw = f.read()
    return html_to_text(raw) if "<html" in raw[:1000].lower() else raw


def clean_line(line):
    return re.sub(r"\s+", " ", line or "").strip()


def section_color(label):
    low = label.lower()
    if "intro" in low:
        return COLORS["intro"]
    if "outro" in low:
        return COLORS["outro"]
    if "pre" in low:
        return COLORS["pre"]
    if "hook" in low or "chorus" in low:
        return COLORS["chorus"]
    if "bridge" in low:
        return COLORS["bridge"]
    if "instrument" in low or "solo" in low or "interlude" in low:
        return COLORS["instrument"]
    if "groove" in low or "vamp" in low:
        return COLORS["groove"]
    return COLORS["verse"]


def plain_section_heading(line):
    text = clean_line(line)
    if not text or "|" in text:
        return ""
    if re.search(r"^(key:|duration:|\d+\s+\d+=|autoscroll|metronome|tools|compact|easy|got it|preferences)$", text, re.I):
        return ""
    if re.search(r"(facts|table|join|cookie|incorrect|request|report)", text, re.I):
        return ""
    if re.fullmatch(
        r"(intro|interlude|instrument(?:s|al)?(?:\s*\([^)]*\))?|verse(?:\s+\d+)?|pre[- ]?chorus(?:\s+\d+)?|"
        r"chorus(?:\s+\d+)?|hook(?:\s+\d+)?|bridge|solo|outro|groove|vamp|"
        r"last[- ]?verse|last[- ]?hook|final[- ]?chorus)(?:\s*[-–—]\s*.+)?",
        text,
        re.I,
    ):
        return text
    return ""


def section_id(label, used):
    base = slugify(label).replace("-", "_") or "section"
    if base[0].isdigit():
        base = "section_" + base
    candidate = base
    idx = 2
    while candidate in used:
        candidate = f"{base}_{idx}"
        idx += 1
    used.add(candidate)
    return candidate


def chord_atom(token):
    root = r"[A-G](?:#|b)?"
    quality = r"(?:maj|min|dim|aug|sus|add|m|M|\+|-|Δ|ø|o)?"
    tail = r"(?:\d+)?(?:[#b]\d+)*(?:sus\d+)?(?:add\d+)?"
    bass = rf"(?:/{root})?"
    pattern = rf"{root}{quality}{tail}{bass}"
    return re.fullmatch(pattern, token or "") is not None


def chord_token(token):
    token = token.strip()
    if not token:
        return False
    if "/" in token and not re.search(r"/[A-G](?:#|b)?$", token):
        return False
    parts = token.split("-")
    return all(chord_atom(part) for part in parts if part)


def parse_chord_segment(segment):
    text = clean_line(segment)
    if not text:
        return None

    time_sig = None
    repeat = None

    def bracket_repl(match):
        nonlocal time_sig, repeat
        value = match.group(1).strip()
        if re.fullmatch(r"\d+\s*/\s*\d+", value):
            time_sig = re.sub(r"\s+", "", value)
            return " "
        if re.fullmatch(r"x\s*\d+", value, re.I):
            repeat = int(re.search(r"\d+", value).group(0))
            return " "
        return match.group(0)

    text = clean_line(re.sub(r"\[([^\]]+)\]", bracket_repl, text))
    if not text:
        return {"bar": None, "repeat": repeat, "time": time_sig}
    if re.fullmatch(r"\d+\s+bars?", text, re.I):
        count = int(re.search(r"\d+", text).group(0))
        return {"placeholder_bars": count, "repeat": repeat, "time": time_sig}

    tokens = text.split()
    if not tokens or not all(chord_token(token) for token in tokens):
        return None

    bar = {"c": "|".join(tokens), "a": "", "h": False}
    if time_sig:
        bar["sn"] = time_sig
    return {"bar": bar, "repeat": repeat, "time": time_sig}


def split_note_cols(lines):
    clean = [clean_line(line) for line in lines if clean_line(line)]
    if not clean:
        return []
    pivot = (len(clean) + 1) // 2 if len(clean) > 7 else len(clean)
    cols = [clean[:pivot], clean[pivot:]]
    return [
        "<p>" + "<br>".join(html.escape(line, quote=False) for line in col) + "</p>" if col else ""
        for col in cols
    ]


def infer_title_artist(lines):
    useful = [
        clean_line(re.sub(r"^#+\s*", "", line))
        for line in lines
        if clean_line(line)
    ]
    skip = {
        "autoscroll", "metronome", "tools", "compact", "easy", "got it",
        "preferences", "join us!", "request song", "report song",
    }
    filtered = [
        line for line in useful
        if line.lower() not in skip
        and not re.search(r"^(key:|duration:|\d+\s+\d+=)", line, re.I)
        and not re.match(r"^(1990s|2000s|pop|rock|english|thai)$", line, re.I)
    ]
    title = filtered[0] if filtered else "New Song"
    artist = filtered[1] if len(filtered) > 1 and not filtered[1].startswith("|") else ""
    return title, artist


def parse_busk_text(text):
    raw_lines = [line.rstrip() for line in text.splitlines()]
    lines = [clean_line(line) for line in raw_lines]
    title, artist = infer_title_artist(lines)

    joined = "\n".join(lines)
    key_match = re.search(r"\bKey:\s*([^\n(]+)", joined, re.I)
    bpm_match = re.search(r"(?:=|tempo[:\s]|bpm[:\s])\s*(\d{2,3})\b", joined, re.I)
    if not bpm_match:
        bpm_match = re.search(r"\b(\d{2,3})\s*bpm\b", joined, re.I)
    time_match = re.search(r"\b([2-9])\s+([24])\s*=", joined)

    payload = {
        "title": title,
        "artist": artist,
        "key": clean_line(key_match.group(1)) if key_match else "",
        "bpm": bpm_match.group(1) if bpm_match else "",
        "time": f"{time_match.group(1)}/{time_match.group(2)}" if time_match else "4/4",
        "vocalist": "",
        "sections": [],
    }
    warnings = []
    used_ids = set()
    current = None
    lyric_lines = []

    def flush_note_for(section):
        nonlocal lyric_lines
        cols = split_note_cols(lyric_lines)
        lyric_lines = []
        if not cols:
            return
        payload["sections"].append({
            "id": section_id("lyric " + section["label"], used_ids),
            "type": "note",
            "label": "Lyric — " + section["label"],
            "cols": cols,
            "color": section["color"],
        })

    def flush_section():
        nonlocal current
        if not current:
            return
        if not current["bars"]:
            current["bars"] = [{"c": "—", "a": "", "h": False}]
            warnings.append(f"{current['label']}: no chord bars found, inserted one blank bar")
        payload["sections"].append(current)
        flush_note_for(current)
        current = None

    def start_section(label):
        nonlocal current
        if current and not current["bars"] and not lyric_lines:
            current = None
        else:
            flush_section()
        current = {
            "id": section_id(label, used_ids),
            "label": label,
            "note": "",
            "noteHidden": True,
            "lyric": "",
            "color": section_color(label),
            "bars": [],
            "rowSizes": [],
        }

    for line in lines:
        if not line:
            continue
        heading = re.match(r"^#{2,3}\s+(.+)$", line)
        label = clean_line(heading.group(1)) if heading else plain_section_heading(line)
        if label:
            if not re.search(r"(facts|table|join|cookie|incorrect|request|report)", label, re.I):
                start_section(label)
            continue
        if not current:
            continue
        if "|" not in line:
            parsed = parse_chord_segment(line)
            if parsed and parsed.get("placeholder_bars"):
                current["bars"].extend({"c": "—", "a": "", "h": False} for _ in range(parsed["placeholder_bars"]))
            elif parsed and parsed.get("bar"):
                current["bars"].append(parsed["bar"])
            elif not re.search(r"^\[?x\s*\d+\]?$", line, re.I):
                lyric_lines.append(line)
            continue

        segments = line.split("|")
        for segment in segments:
            segment = clean_line(segment)
            if not segment:
                continue
            parsed = parse_chord_segment(segment)
            if not parsed:
                lyric_lines.append(segment)
                continue
            repeat = parsed.get("repeat")
            if parsed.get("placeholder_bars"):
                current["bars"].extend({"c": "—", "a": "", "h": False} for _ in range(parsed["placeholder_bars"]))
            elif parsed.get("bar"):
                current["bars"].append(parsed["bar"])
            if repeat:
                if repeat > 9:
                    warnings.append(f"{current['label']}: repeat x{repeat} capped/left for review")
                group = "A"
                current["rowSizes"] = [min(len(current["bars"]), 8)]
                current["rowRepeatGroups"] = {"0": group}
                current["repeatCounts"] = {group: min(max(repeat, 2), 9)}

    flush_section()
    if not payload["sections"]:
        raise ValueError("no Busk sections found; paste text with headings like Verse 1 or ## Verse 1")
    payload["_warnings"] = warnings
    return payload


def write_json(path, payload):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
        f.write("\n")


def generate_html(payload, output="", band=""):
    checked = {
        **payload,
        "sections": payload["sections"],
    }
    checked.pop("_warnings", None)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", suffix=".json", delete=False) as tmp:
        json.dump(checked, tmp, ensure_ascii=False)
        tmp_path = tmp.name
    try:
        clean = bandsheet_import.load_payload(tmp_path)
        with open(bandsheet_import.TEMPLATE_PATH, encoding="utf-8") as f:
            template = f.read()
        out = output
        if not out:
            if not band:
                raise ValueError("provide --band or --output to write HTML")
            out = os.path.join(BAND_ROOT, band, slugify(clean["title"]) + ".html")
        out = os.path.abspath(out)
        if not out.startswith(BAND_ROOT + os.sep):
            raise ValueError("output must be inside the bandsheet project")
        os.makedirs(os.path.dirname(out), exist_ok=True)
        with open(out, "w", encoding="utf-8") as f:
            f.write(bandsheet_import.inject(template, clean))
        return out
    finally:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass


def main():
    parser = argparse.ArgumentParser(description="Convert Busk chord text or URL into Bandsheet JSON/HTML.")
    parser.add_argument("source", nargs="?", help="Busk URL, local text/html file, or - for stdin")
    parser.add_argument("--json", default="", help="Write parsed Bandsheet JSON to this path")
    parser.add_argument("--check", action="store_true", help="Validate parsed JSON with bandsheet_import.py")
    parser.add_argument("--band", default="", help="Band folder for generated HTML")
    parser.add_argument("--output", default="", help="Generated HTML output path")
    args = parser.parse_args()

    try:
        payload = parse_busk_text(read_source(args.source))
        json_path = args.json
        if json_path:
            write_json(json_path, payload)
            print(f"OK wrote JSON: {os.path.relpath(os.path.abspath(json_path), BAND_ROOT)}")
        if args.check:
            with tempfile.NamedTemporaryFile("w", encoding="utf-8", suffix=".json", delete=False) as tmp:
                clean_payload = dict(payload)
                clean_payload.pop("_warnings", None)
                json.dump(clean_payload, tmp, ensure_ascii=False)
                tmp_path = tmp.name
            try:
                checked = bandsheet_import.load_payload(tmp_path)
                print(f"OK valid input: {len(checked['sections'])} sections")
            finally:
                os.unlink(tmp_path)
        if args.output or args.band:
            out = generate_html(payload, args.output, args.band)
            print(f"OK wrote HTML: {os.path.relpath(out, BAND_ROOT)}")
        if not (json_path or args.check or args.output or args.band):
            print(json.dumps(payload, ensure_ascii=False, indent=2))
        for warning in payload.get("_warnings", []):
            print(f"WARN {warning}", file=sys.stderr)
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
