#!/usr/bin/env python3
import os, re, json

BAND_ROOT = os.path.dirname(os.path.abspath(__file__))
SKIP_DIRS = {"backup", ".git", ".claude", "PDF", "Backup", "__pycache__", "node_modules"}
SKIP_FILES = {"index.html", "_template.html", "generate_bandsheets.py",
              "update_index.py", "push.sh", "Online Bandsheet.md", "CLAUDE.md"}

def extract_meta(filepath):
    try:
        with open(filepath, encoding="utf-8") as f:
            html = f.read()
    except Exception:
        return None
    def get_val(fid):
        m = re.search(r'id="' + re.escape(fid) + r'"[^>]*value="([^"]*)"', html)
        return m.group(1).strip() if m else ""
    title = get_val("tb-filename")
    artist = get_val("tb-artist")
    for pfx in ["— ", "- "]:
        if artist.startswith(pfx):
            artist = artist[len(pfx):]
    key = get_val("meta-key")
    bpm = get_val("meta-bpm")
    if not title:
        m = re.search(r"<title>([^<]+?)\s*\xb7", html)
        if m:
            title = m.group(1).strip()
    if not title:
        return None
    return {"title": title, "artist": artist, "key": key, "bpm": bpm,
            "bars": "", "file": os.path.basename(filepath)}

def read_existing_setlists(index_path):
    """Read existing SONGS array and return {filename: setlist_value} mapping."""
    try:
        with open(index_path, encoding="utf-8") as f:
            content = f.read()
        m = re.search(r'var SONGS\s*=\s*(\[.*?\]);\s*//[^\n]*END SONGS', content, re.DOTALL)
        if m:
            existing = json.loads(m.group(1))
            return {s["file"]: s.get("setlist", "") for s in existing if "file" in s}
    except Exception:
        pass
    return {}

def update_band_index(band_dir):
    index_path = os.path.join(band_dir, "index.html")
    if not os.path.exists(index_path):
        print(f"  skip {os.path.basename(band_dir)} - no index.html")
        return 0
    existing_setlists = read_existing_setlists(index_path)
    html_files = sorted([f for f in os.listdir(band_dir)
                         if f.endswith(".html") and f not in SKIP_FILES])
    songs = [m for f in html_files
             for m in [extract_meta(os.path.join(band_dir, f))] if m]
    # Preserve setlist values from existing index
    for s in songs:
        s["setlist"] = existing_setlists.get(s["file"], "")
    with open(index_path, encoding="utf-8") as f:
        idx = f.read()
    songs_json = json.dumps(songs, ensure_ascii=False, indent=2)
    repl = "var SONGS = " + songs_json + "; // -- END SONGS --"
    pat = r"var SONGS\s*=\s*\[.*?\];\s*//[^\n]*END SONGS[^\n]*"
    # Use search first to confirm marker exists, then sub
    if not re.search(pat, idx, flags=re.DOTALL):
        print(f"  WARNING: marker not found in {os.path.basename(band_dir)}/index.html")
        return 0
    new_idx = re.sub(pat, repl, idx, flags=re.DOTALL)
    with open(index_path, "w", encoding="utf-8") as f:
        f.write(new_idx)
    print(f"  OK {os.path.basename(band_dir)}/index.html - {len(songs)} songs")
    return len(songs)

def main():
    print("Bandsheet Index Updater")
    print("-" * 40)
    dirs = [os.path.join(BAND_ROOT, n) for n in sorted(os.listdir(BAND_ROOT))
            if os.path.isdir(os.path.join(BAND_ROOT, n))
            and n not in SKIP_DIRS and not n.startswith(".")]
    total = sum(update_band_index(d) for d in dirs)
    print("-" * 40)
    print(f"Done - {total} songs across {len(dirs)} bands")

if __name__ == "__main__":
    main()
