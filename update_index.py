#!/usr/bin/env python3
import html
import json
import os
import re
import subprocess

BAND_ROOT = os.path.dirname(os.path.abspath(__file__))
VERSION = "bandsheet v6.17"
UPDATED = "2026-06-02"

SKIP_DIRS = {"backup", "_archive", ".git", ".claude", "PDF", "pdf", "Backup", "__pycache__", "node_modules", "Note Values", "90alter"}
SKIP_FILES = {
    "index.html",
    "_template.html",
    "generate_bandsheets.py",
    "update_index.py",
    "push.sh",
    "Online Bandsheet.md",
    "CLAUDE.md",
    "bandsheet_workflow_summary.html",
    "_prototype-rhythm-strip.html",
    "bluebird-jazz.html",
}

BAND_META = {
    "ti-muse": {"name": "ti.muse", "color": "#60a5fa"},
    "the-maewjons": {"name": "THE MÆWJØNS", "color": "#EB3C1F"},
    "parkhaus108": {"name": "PARKHAUS108", "color": "#6D132D"},
    "parkhaus-studio": {"name": "PARKHAUS Studio", "color": "#6D132D"},
}

BAND_ORDER = ["ti-muse", "the-maewjons", "parkhaus108", "parkhaus-studio"]

PDF_LINKS = [
    {
        "bandId": "parkhaus108",
        "label": "pdf · PARKHAUS108",
        "href": "parkhaus108/2026-06-27-PARKHAUS108.pdf",
        "color": "#6D132D",
    },
]

PROJECT_LINKS = [
    {
        "bandId": "the-maewjons",
        "label": "project · Bluebird",
        "href": "the-maewjons/bluebird-jazz.html",
        "color": "#EB3C1F",
    },
]


def read_text(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


def write_text(path, content):
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def js_json(data):
    return json.dumps(data, ensure_ascii=False, indent=2)


def git_value(fmt):
    try:
        return subprocess.check_output(
            ["git", "log", "-1", "--format=" + fmt],
            cwd=BAND_ROOT,
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except Exception:
        return ""


def get_input_value(doc, field_id):
    m = re.search(r'id="' + re.escape(field_id) + r'"[^>]*value="([^"]*)"', doc)
    return html.unescape(m.group(1)).strip() if m else ""


def count_bars(doc):
    marker = "// ── END DATA ──"
    decl = "var SECTIONS = "
    marker_pos = doc.find(marker)
    if marker_pos < 0:
        return ""
    start = doc.rfind(decl, 0, marker_pos)
    if start < 0:
        return ""
    payload = doc[start + len(decl):marker_pos].strip()
    if payload.endswith(";"):
        payload = payload[:-1].strip()
    try:
        sections = json.loads(payload)
    except Exception:
        return ""

    total = 0
    for section in sections:
        bars = section.get("bars") if isinstance(section, dict) else None
        if not isinstance(bars, list):
            continue
        total += sum(1 for bar in bars if not (isinstance(bar, dict) and bar.get("skipCount")))
    return str(total) if total else ""


def validate_pdf_links(bands):
    band_ids = {band["id"] for band in bands}
    for item in PDF_LINKS:
        band_id = item.get("bandId", "")
        href = item.get("href", "")
        if band_id not in band_ids:
            raise ValueError(f"PDF link uses unknown bandId: {band_id}")
        if not href or os.path.isabs(href) or ".." in href.split("/"):
            raise ValueError(f"PDF link must be a project-relative path: {href}")
        if not os.path.exists(os.path.join(BAND_ROOT, href)):
            raise ValueError(f"PDF link target is missing: {href}")


def title_from_filename(filepath):
    name = os.path.splitext(os.path.basename(filepath))[0]
    name = re.sub(r"^\d+[-_\s]+", "", name)
    return " ".join(part.capitalize() for part in re.split(r"[-_\s]+", name) if part)


def extract_meta(filepath):
    try:
        doc = read_text(filepath)
    except Exception:
        return None

    title = get_input_value(doc, "tb-filename")
    artist = get_input_value(doc, "tb-artist")
    for prefix in ("— ", "- "):
        if artist.startswith(prefix):
            artist = artist[len(prefix):].strip()

    if not title or title.lower() in {"song title", "new song"}:
        m = re.search(r"<title>([^<]+?)\s*·", doc)
        if m:
            title = html.unescape(m.group(1)).strip()
    if not title or title.lower() in {"song title", "new song"}:
        title = title_from_filename(filepath)
    if not title:
        return None
    if artist.lower() in {"artist", "song artist"}:
        artist = ""

    return {
        "title": title,
        "artist": artist,
        "key": get_input_value(doc, "meta-key"),
        "bpm": get_input_value(doc, "meta-bpm"),
        "vocalist": get_input_value(doc, "meta-vocalist"),
        "bars": count_bars(doc),
        "file": os.path.basename(filepath),
    }


def read_existing_setlists(index_path):
    try:
        doc = read_text(index_path)
        m = re.search(r"var SONGS\s*=\s*(\[.*?\]);", doc, re.DOTALL)
        if not m:
            m = re.search(r"var ALL_SONGS\s*=\s*(\[.*?\]);\s*//[^\n]*END ALL SONGS", doc, re.DOTALL)
        if not m:
            return {}
        existing = json.loads(m.group(1))
        out = {}
        for song in existing:
            file_name = song.get("file")
            band_id = song.get("bandId", "")
            value = song.get("setlist", "")
            if file_name:
                out[(band_id, file_name)] = value
                out[("", file_name)] = value
        return out
    except Exception:
        return {}


def discover_bands():
    found = []
    for name in sorted(os.listdir(BAND_ROOT)):
        path = os.path.join(BAND_ROOT, name)
        if not os.path.isdir(path) or name in SKIP_DIRS or name.startswith("."):
            continue
        if not os.path.exists(os.path.join(path, "index.html")):
            continue
        meta = BAND_META.get(name, {"name": name, "color": "#888888"})
        found.append({
            "id": name,
            "name": meta["name"],
            "color": meta["color"],
            "path": name + "/",
            "indexHref": name + "/index.html",
        })
    found.sort(key=lambda b: BAND_ORDER.index(b["id"]) if b["id"] in BAND_ORDER else 999)
    return found


def collect_songs(bands):
    setlists = {}
    for band in bands:
        setlists.update(read_existing_setlists(os.path.join(BAND_ROOT, band["id"], "index.html")))

    songs = []
    for band in bands:
        band_dir = os.path.join(BAND_ROOT, band["id"])
        html_files = sorted(
            f for f in os.listdir(band_dir)
            if f.endswith(".html") and f not in SKIP_FILES
        )
        for file_name in html_files:
            song = extract_meta(os.path.join(band_dir, file_name))
            if not song:
                continue
            song["bandId"] = band["id"]
            song["bandName"] = band["name"]
            song["bandColor"] = band["color"]
            song["href"] = band["path"] + file_name
            song["setlist"] = setlists.get((band["id"], file_name), setlists.get(("", file_name), ""))
            songs.append(song)

    counts = {band["id"]: 0 for band in bands}
    for song in songs:
        counts[song["bandId"]] += 1
    for band in bands:
        band["songCount"] = counts[band["id"]]
    return songs


def render_version_badge():
    return f"{VERSION} · updated {UPDATED}"


def render_project_links(current_band=None):
    links = []
    for item in PROJECT_LINKS:
        if current_band and item["bandId"] != current_band:
            continue
        href = item["href"]
        if current_band:
            prefix = current_band + "/"
            if href.startswith(prefix):
                href = href[len(prefix):]
        links.append(
            '<a class="toolbar-link accent-link" style="--item-color:'
            + html.escape(item.get("color", "#60758d"), quote=True)
            + '" href="'
            + html.escape(href, quote=True)
            + '">'
            + html.escape(item["label"])
            + "</a>"
        )
    return "".join(links)


def render_pdf_links(current_band=None):
    links = []
    for item in PDF_LINKS:
        if current_band and item["bandId"] != current_band:
            continue
        href = item["href"]
        if current_band:
            prefix = current_band + "/"
            if href.startswith(prefix):
                href = href[len(prefix):]
        links.append(
            '<a class="toolbar-link accent-link" style="--item-color:'
            + html.escape(item.get("color", "#60758d"), quote=True)
            + '" href="'
            + html.escape(href, quote=True)
            + '" target="_blank" rel="noopener">'
            + html.escape(item["label"])
            + "</a>"
        )
    return "".join(links)


STYLE = """
:root{--bg:#f7f9fc;--surface:#fff;--border:#dfe7f2;--border-strong:#c8d4e3;--text:#172033;--text-muted:#7d8ca0;--text-faint:#b7c3d1;--ui-ink:#5f6f83;--ui-muted:#9aa8ba;--ui-line:#e6edf5;--ui-soft:#f3f7fb;--ui-hover:#edf3f9;--ui-active:#60758d;--accent:#3b82f6}
*{box-sizing:border-box;margin:0;padding:0}
body{background:var(--bg);color:var(--text);font-family:'IBM Plex Sans Thai','Inter',sans-serif;min-height:100vh;padding-bottom:48px}
a{color:inherit}
header{background:var(--surface);border-bottom:1px solid var(--border);padding:26px 0 18px}
.page-shell{max-width:1160px;margin:0 auto;padding:0 38px}
.breadcrumb{font-family:'Inter',sans-serif;font-size:11px;color:var(--ui-muted);letter-spacing:.012em;margin-bottom:10px}
.breadcrumb a{color:var(--ui-muted);text-decoration:none}.breadcrumb a:hover{color:var(--ui-ink)}
.site-label,.section-label{font-family:'Inter',sans-serif;font-size:10px;font-weight:700;letter-spacing:.1em;text-transform:uppercase;color:var(--ui-muted)}
h1{font-family:'Inter',sans-serif;font-size:26px;font-weight:600;line-height:1.18;letter-spacing:0;margin-top:6px;color:var(--text)}
.sub,.stats{font-size:12px;color:var(--text-muted);margin-top:6px}
.version-pill{display:inline-flex;font-family:'Inter',sans-serif;font-size:10px;font-weight:600;letter-spacing:.07em;text-transform:uppercase;color:var(--ui-ink);border:1px solid var(--border-strong);background:var(--ui-soft);border-radius:4px;padding:4px 9px;margin-top:12px}
.toolbar{position:sticky;top:0;z-index:40;background:rgba(255,255,255,.96);-webkit-backdrop-filter:blur(16px);backdrop-filter:blur(16px);border-bottom:1px solid var(--ui-line);padding:10px 0}
.toolbar-inner{display:flex;align-items:center;gap:8px;flex-wrap:wrap}
.search-wrap{position:relative;flex:1 1 260px;max-width:430px}.search-icon{position:absolute;left:10px;top:50%;transform:translateY(-50%);color:var(--ui-muted);font-size:13px;pointer-events:none}
.search,.filter-input{font-family:'Inter',sans-serif;font-size:12px;font-weight:300;background:var(--ui-soft);border:none;color:var(--ui-ink);border-radius:5px;padding:7px 10px;outline:none;width:100%;transition:background .12s,color .12s,box-shadow .12s}.search{padding-left:30px}.search:focus,.filter-input:focus{background:var(--ui-hover);color:var(--text);box-shadow:inset 0 0 0 1px var(--border-strong)}.search::placeholder,.filter-input::placeholder{color:var(--ui-muted)}
.filter-group{display:flex;align-items:center;gap:5px;flex-wrap:wrap}.filter-label{font-family:'Inter',sans-serif;font-size:10px;color:var(--ui-muted);letter-spacing:.08em;text-transform:uppercase;white-space:nowrap}
.filter-field{display:flex;align-items:center;gap:6px}.filter-field .filter-input{width:104px}.filter-field.vocalist .filter-input{width:150px}
.filter-pill,.clear-btn{font-family:'Inter',sans-serif;font-size:10px;font-weight:500;padding:5px 9px;border:1px solid var(--border);border-radius:4px;background:var(--surface);color:var(--text-muted);cursor:pointer;transition:background .12s,border-color .12s,color .12s;white-space:nowrap}
.filter-pill{position:relative;overflow:hidden;padding-left:13px}.filter-pill::before{content:'';position:absolute;left:0;top:0;bottom:0;width:3px;background:var(--item-color,var(--accent));opacity:.9}
.filter-pill:hover,.clear-btn:hover{background:var(--ui-hover);border-color:var(--border-strong);color:var(--ui-ink)}.filter-pill.active{background:var(--ui-active);border-color:var(--ui-active);color:#f8fbff}.filter-pill.active::before{background:#f8fbff;opacity:.75}
.toolbar-link{font-family:'Inter',sans-serif;font-size:12px;font-weight:400;padding:4px 8px;border:1px solid transparent;border-radius:6px;background:transparent;color:var(--ui-ink);text-decoration:none;cursor:pointer;transition:background .1s,color .1s,border-color .1s;white-space:nowrap;height:27px;display:inline-flex;align-items:center;letter-spacing:.012em;text-transform:lowercase}
.toolbar-link.accent-link{position:relative;overflow:hidden;padding-left:13px;border-color:var(--border);background:var(--surface);color:var(--text-muted)}
.toolbar-link.accent-link::before{content:'';position:absolute;left:0;top:0;bottom:0;width:3px;background:var(--item-color,var(--accent))}
.toolbar-link:hover{background:var(--ui-hover);border-color:var(--border-strong);color:var(--ui-ink)}
main{padding:22px 38px 50px;max-width:1160px;margin:0 auto}
.band-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(160px,1fr));gap:8px;margin:8px 0 24px}
.band-card{display:block;text-decoration:none;background:var(--surface);border:1px solid var(--border);border-radius:6px;padding:11px 13px 11px 15px;position:relative;overflow:hidden;transition:border-color .15s,background .15s}.band-card:hover{border-color:var(--border-strong);background:#fbfdff}.band-card:before{content:'';position:absolute;left:0;top:0;bottom:0;width:3px;background:var(--band-color)}
.band-name{font-family:'Inter',sans-serif;font-size:12px;font-weight:600;color:var(--text)}.band-song-count{font-family:'Inter',sans-serif;font-size:10px;color:var(--text-muted);margin-top:3px}
.table-wrap{width:100%;overflow-x:auto}.song-table{width:100%;border-collapse:collapse;min-width:820px;margin-top:8px}.song-table th{font-family:'Inter',sans-serif;font-size:9px;font-weight:700;letter-spacing:.12em;text-transform:uppercase;color:var(--ui-muted);text-align:left;padding:11px 10px 9px;border-bottom:1px solid var(--border);white-space:nowrap}.song-table th:first-child{padding-left:0;width:38px}
.song-row{border-bottom:1px solid var(--ui-line);transition:background .1s;cursor:pointer}.song-row:hover{background:rgba(255,255,255,.72)}.song-row:focus-visible{outline:2px solid var(--border-strong);outline-offset:-2px;background:#fff}.song-row td{padding:12px 10px;font-size:13px;vertical-align:middle}.song-row td:first-child{padding-left:0}
.song-num,.song-key,.song-bpm,.song-band,.song-vocalist{font-family:'Inter',sans-serif;font-size:11px;color:var(--text-muted);white-space:nowrap}.song-title{font-weight:600;color:var(--text);overflow-wrap:anywhere}.song-artist,.song-vocalist-sub{font-size:11px;color:var(--text-muted);margin-top:2px;overflow-wrap:anywhere}
.band-dot{width:8px;height:8px;border-radius:50%;display:inline-block;margin-right:6px}
.setlist-input{font-family:'Inter',sans-serif;font-size:12px;background:transparent;border:1px solid transparent;border-radius:4px;color:var(--text-muted);width:42px;text-align:center;padding:2px 4px;outline:none}.setlist-input:hover,.setlist-input:focus{border-color:var(--border-strong);color:var(--text);background:var(--surface)}
.th-sortable{cursor:pointer;user-select:none}.th-sortable:hover{color:var(--ui-ink)}.sort-ind{font-size:9px;opacity:.45;margin-left:2px;text-transform:lowercase}.sort-ind.on{opacity:1;color:var(--ui-active)}
.empty{padding:34px 0;color:var(--text-muted);font-size:13px}.hidden{display:none!important}footer{max-width:1160px;margin:0 auto;padding:18px 38px;border-top:1px solid var(--border);font-size:11px;color:var(--text-muted);font-family:'Inter',sans-serif;display:flex;justify-content:space-between;gap:12px;flex-wrap:wrap}
@media(max-width:820px){header{padding:24px 0 16px}.page-shell{padding:0 18px}.toolbar{padding:10px 0}.toolbar-inner{align-items:stretch}.search-wrap{max-width:none;flex-basis:100%}.filter-group{width:100%}.filter-field{flex:1 1 132px}.filter-field .filter-input,.filter-field.vocalist .filter-input{width:100%}main{padding:18px 18px 44px}.band-grid{grid-template-columns:repeat(2,minmax(0,1fr))}.song-table{min-width:700px}.song-table th,.song-row td{padding-left:8px;padding-right:8px}footer{padding:18px}}
"""


SCRIPT = """
var activeBand = CURRENT_BAND || 'all';
var sortCol = 'default';
var sortDir = 1;

function esc(s){return String(s == null ? '' : s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');}
function splitVocalists(v){
  return String(v || '').split(/[,/&+]|\\band\\b|\\bfeat\\.?\\b|\\bft\\.?\\b/i).map(function(x){return x.trim();}).filter(Boolean);
}
function vocalistKey(v){return v.toLowerCase();}
function getVisibleSongs(){
  var q = document.getElementById('search').value.toLowerCase().trim();
  var keyQ = (document.getElementById('key-filter') || {}).value || '';
  var vocalistQ = (document.getElementById('vocalist-filter') || {}).value || '';
  keyQ = keyQ.toLowerCase().trim();
  vocalistQ = vocalistQ.toLowerCase().trim();
  return ALL_SONGS.filter(function(s){
    var search = [s.title,s.artist,s.key,s.bpm,s.bandName,s.vocalist].join(' ').toLowerCase();
    return (!q || search.indexOf(q) !== -1) &&
      (activeBand === 'all' || s.bandId === activeBand) &&
      (!keyQ || String(s.key || '').toLowerCase().indexOf(keyQ) !== -1) &&
      (!vocalistQ || splitVocalists(s.vocalist).some(function(v){return vocalistKey(v).indexOf(vocalistQ) !== -1;}));
  }).sort(function(a,b){
    if(sortCol === 'setlist'){
      var sa = parseInt(a.setlist)||0, sb = parseInt(b.setlist)||0;
      if(!sa && !sb) return (a.title||'').localeCompare(b.title||'');
      if(!sa) return 1;
      if(!sb) return -1;
      return (sa - sb) * sortDir;
    }
    if(sortCol === 'title') return (a.title||'').localeCompare(b.title||'') * sortDir;
    if(sortCol === 'vocalist') return ((a.vocalist||'zzzz')+' '+(a.title||'')).localeCompare((b.vocalist||'zzzz')+' '+(b.title||'')) * sortDir;
    return 0;
  });
}
function buildBandCards(){
  var grid = document.getElementById('band-grid');
  if(!grid) return;
  grid.innerHTML = ALL_BANDS.map(function(b){
    return '<a class="band-card" href="'+esc(b.indexHref || b.path)+'" style="--band-color:'+esc(b.color)+'">' +
      '<div class="band-name">'+esc(b.name)+'</div>' +
      '<div class="band-song-count">'+b.songCount+' songs</div></a>';
  }).join('');
}
function importerHref(){
  var href = '_work/busk-import.html';
  if(activeBand && activeBand !== 'all') href += '?band=' + encodeURIComponent(activeBand);
  return href;
}
function syncImporterLink(){
  var link = document.getElementById('importer-link');
  if(!link) return;
  link.href = importerHref();
  var band = activeBand === 'all' ? '' : (ALL_BANDS.find(function(b){return b.id===activeBand;})||{}).name;
  link.textContent = band ? 'importer · ' + band : 'importer';
}
function buildFilters(){
  var bf = document.getElementById('band-filters');
  if(bf){
    bf.innerHTML = '<span class="filter-label">Band:</span>' +
      '<button class="filter-pill" style="--item-color:#60758d" data-band="all" onclick="setBandFilter(\\'all\\')">All</button>' +
      ALL_BANDS.map(function(b){return '<button class="filter-pill" style="--item-color:'+esc(b.color)+'" data-band="'+esc(b.id)+'" onclick="setBandFilter(\\''+esc(b.id)+'\\')">'+esc(b.name)+'</button>';}).join('');
  }
  syncFilterState();
}
function syncFilterState(){
  document.querySelectorAll('[data-band]').forEach(function(el){el.classList.toggle('active', el.dataset.band === activeBand);});
  syncImporterLink();
}
function renderSongs(){
  var songs = getVisibleSongs();
  var tbody = document.getElementById('song-list');
  var empty = document.getElementById('empty-state');
  tbody.innerHTML = songs.map(function(s,i){
    var href = IS_ROOT ? s.href : s.file;
    var bandCell = IS_ROOT ? '<td class="song-band"><span class="band-dot" style="background:'+esc(s.bandColor)+'"></span>'+esc(s.bandName)+'</td>' : '';
    return '<tr class="song-row" data-href="'+esc(href)+'" tabindex="0" onclick="openSongRow(event,this)" onkeydown="openSongRowKey(event,this)">' +
      '<td class="song-num">'+String(i+1).padStart(2,'0')+'</td>' +
      '<td><input class="setlist-input" type="text" value="'+esc(s.setlist||'')+'" readonly title="Generated from index source" onclick="event.stopPropagation()"></td>' +
      '<td><div class="song-title">'+esc(s.title)+'</div><div class="song-artist">'+esc(s.artist || '-')+'</div></td>' +
      '<td class="song-key">'+esc(s.key || '-')+'</td>' +
      '<td class="song-bpm">'+esc(s.bpm || '-')+'</td>' +
      '<td class="song-vocalist">'+esc(s.vocalist || '-')+'</td>' +
      bandCell +
      '</tr>';
  }).join('');
  empty.classList.toggle('hidden', songs.length !== 0);
  var label = activeBand === 'all' ? 'all bands' : (ALL_BANDS.find(function(b){return b.id===activeBand;})||{}).name;
  document.getElementById('stats').textContent = songs.length + ' songs · ' + label;
  var ind = document.getElementById('sort-set-ind');
  if(ind){ind.textContent = sortCol === 'setlist' ? (sortDir === 1 ? 'up' : 'down') : 'sort'; ind.className = 'sort-ind' + (sortCol === 'setlist' ? ' on' : '');}
  var vind = document.getElementById('sort-vocalist-ind');
  if(vind){vind.textContent = sortCol === 'vocalist' ? (sortDir === 1 ? 'up' : 'down') : 'sort'; vind.className = 'sort-ind' + (sortCol === 'vocalist' ? ' on' : '');}
}
function openSongRow(event,row){
  if(event.defaultPrevented || event.target.closest('input,button,a,select,textarea')) return;
  var href = row.getAttribute('data-href');
  if(href){
    var win = window.open(href, '_blank');
    if(win) win.opener = null;
  }
}
function openSongRowKey(event,row){
  if(event.key !== 'Enter' && event.key !== ' ') return;
  event.preventDefault();
  var href = row.getAttribute('data-href');
  if(href){
    var win = window.open(href, '_blank');
    if(win) win.opener = null;
  }
}
function setBandFilter(id){activeBand = id; syncFilterState(); renderSongs();}
function setSortBy(col){if(sortCol === col){sortDir = -sortDir;}else{sortCol = col; sortDir = 1;} renderSongs();}
function clearFilters(){document.getElementById('search').value=''; document.getElementById('key-filter').value=''; document.getElementById('vocalist-filter').value=''; activeBand = CURRENT_BAND || 'all'; sortCol = 'default'; sortDir = 1; buildFilters(); renderSongs();}
function init(){buildBandCards(); buildFilters(); renderSongs();}
init();
"""


def render_index(bands, songs, current_band=None):
    is_root = current_band is None
    band = next((b for b in bands if b["id"] == current_band), None)
    title = "Bandsheet · ti.muse" if is_root else f"{band['name']} · Bandsheet"
    heading = "bandsheet by ti.muse" if is_root else band["name"]
    label = "Band Sheet Archive" if is_root else "Band index"
    subtitle = "Search songs by band, key, BPM, vocalist, or artist" if is_root else f"{band['songCount']} songs · searchable by key, vocalist, and artist"
    breadcrumb = "" if is_root else '<div class="breadcrumb"><a href="../">Band Sheet</a> / ' + html.escape(band["name"]) + "</div>"
    band_cards = ""
    band_filter = '<div class="filter-group" id="band-filters"></div>' if is_root else ""
    band_header = "<th>Band</th>" if is_root else ""
    importer_link = '<a class="toolbar-link" id="importer-link" href="_work/busk-import.html">importer</a>' if is_root else ""
    project_links = render_project_links(current_band)
    pdf_links = render_pdf_links(current_band)
    current = "null" if is_root else json.dumps(current_band)
    body_class = "root-index" if is_root else "band-index"
    home_link = "" if is_root else '<span><a href="../" style="color:var(--muted);text-decoration:none">back to all bands</a></span>'
    version_badge = render_version_badge()

    return f"""<!DOCTYPE html>
<html lang="th">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{html.escape(title)}</title>
<link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans+Thai:wght@300;400;500;600&family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
<style>{STYLE}</style>
</head>
<body class="{body_class}">
<header>
  <div class="page-shell">
    {breadcrumb}
    <div class="site-label">{html.escape(label)}</div>
    <h1>{html.escape(heading)}</h1>
    <p class="sub">{html.escape(subtitle)}</p>
    <div class="version-pill">{html.escape(version_badge)}</div>
  </div>
</header>
<div class="toolbar">
  <div class="page-shell toolbar-inner">
    <div class="search-wrap">
      <span class="search-icon">⌕</span>
      <input class="search" id="search" type="text" placeholder="Search songs, artists, vocalist, key, BPM..." oninput="renderSongs()" autocomplete="off">
    </div>
    {band_filter}
    <label class="filter-field key" for="key-filter">
      <span class="filter-label">Key:</span>
      <input class="filter-input" id="key-filter" type="text" placeholder="A, Dm..." oninput="renderSongs()" autocomplete="off">
    </label>
    <label class="filter-field vocalist" for="vocalist-filter">
      <span class="filter-label">Vocal:</span>
      <input class="filter-input" id="vocalist-filter" type="text" placeholder="name..." oninput="renderSongs()" autocomplete="off">
    </label>
    <button class="clear-btn" onclick="clearFilters()">Clear</button>
    {project_links}
    {pdf_links}
    {importer_link}
  </div>
</div>
<main>
  {band_cards}
  <section>
    <div class="section-label" id="stats"></div>
    <div class="table-wrap">
      <table class="song-table">
        <thead><tr><th>#</th><th class="th-sortable" onclick="setSortBy('setlist')">Set <span class="sort-ind" id="sort-set-ind">sort</span></th><th class="th-sortable" onclick="setSortBy('title')">Song / Artist</th><th>Key</th><th>BPM</th><th class="th-sortable" onclick="setSortBy('vocalist')">Vocalist <span class="sort-ind" id="sort-vocalist-ind">sort</span></th>{band_header}</tr></thead>
        <tbody id="song-list"></tbody>
      </table>
    </div>
    <div class="empty hidden" id="empty-state">No songs found. Try clearing search or filters.</div>
  </section>
</main>
<footer><span>vault.ti.muse / bandsheet</span>{home_link}</footer>
<script>
var BANDS = {js_json(bands)};
var SONGS = {js_json(songs)};
var ALL_BANDS = BANDS;
var ALL_SONGS = SONGS;
var CURRENT_BAND = {current};
var IS_ROOT = {str(is_root).lower()};
{SCRIPT}
</script>
</body>
</html>
"""


def main():
    print("Bandsheet Index Updater")
    print("-" * 40)
    bands = discover_bands()
    validate_pdf_links(bands)
    songs = collect_songs(bands)

    write_text(os.path.join(BAND_ROOT, "index.html"), render_index(bands, songs))
    print(f"  OK index.html - {len(songs)} songs across {len(bands)} bands")

    for band in bands:
        band_songs = [song for song in songs if song["bandId"] == band["id"]]
        write_text(os.path.join(BAND_ROOT, band["id"], "index.html"), render_index(bands, band_songs, band["id"]))
        print(f"  OK {band['id']}/index.html - {len(band_songs)} songs")

    print("-" * 40)
    print(f"Done - {len(songs)} songs across {len(bands)} bands")


if __name__ == "__main__":
    main()
