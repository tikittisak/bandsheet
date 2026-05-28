# Bandsheet Project — Codex Instructions

## Project Overview
สร้าง band sheet HTML จาก chord chart ที่ user ให้มา
Template อยู่ที่ `_template.html` — **current version: v6.03**

---

## Workflow ทุกครั้งที่รับคำสั่ง

### Step 1 — หา Metadata (web search)
ค้นหาเฉพาะ:
- **Key** (เช่น F major, D minor)
- **BPM**
- **Time signature** (เกือบทั้งหมดเป็น 4/4)
- **Song structure** — ชื่อ section และลำดับ (Intro / Verse / Pre-Chorus / Chorus / Bridge / Solo / Outro)

Sources ที่ดีที่สุด: Tunebat → Songdata.io → SongBPM
**ห้ามหา chord จาก web** — user จะให้ chord มาเอง

### Step 2 — รับ Chord Chart จาก User
User จะ paste text หรือ upload image chord chart มาให้
รอจนกว่าจะได้รับก่อน generate

### Step 3 — Parse Chord Chart
แปลง chord chart เป็น SECTIONS JSON ตาม format ด้านล่าง

### Step 4 — Generate HTML
Read `_template.html` → inject ข้อมูล → save เป็น `{band-folder}/{song-title}.html`
(ไม่ต้อง copy ก่อน — inject แล้ว write ไปยัง path ใหม่ตรงๆ)

---

## File Structure
```
Bandsheet/
├── AGENTS.md
├── _template.html               ← template v6.03
├── bandsheet_import.py          ← validate/sanitize/import AI JSON
├── update_index.py              ← rebuild root + band indexes
├── push.sh                      ← update index + commit + push
├── backup/                      ← เก็บ snapshot ของแต่ละ version
├── wait-for-delete/             ← ของเก่า/ต้นแบบที่แยกไว้ก่อนลบจริง
├── the-maewjons/
│   └── virtual-insanity.html
└── parkhaus108/
    ├── index.html
    └── stay-with-me.html
```

**Version bump workflow:**
1. Backup ไฟล์ปัจจุบันไปที่ `backup/{name}-v{current}.html`
2. แก้ `_template.html` + song files ทุกไฟล์พร้อมกัน (ใช้ Python script)
3. อัพเดต version badge ใน template และ AGENTS.md

---

## UI Iteration Workflow
- ระหว่าง iterate UI / review visual / browser comments ให้แก้เฉพาะ `_template.html` ก่อน
- ห้าม sync ทุก micro-change ไป song sheets ระหว่าง review
- sync `_template.html` ไป song sheets เฉพาะหลัง user confirm ว่า design/behavior ถูกต้องแล้ว
- ก่อน go online เท่านั้น ค่อย run `python3 update_index.py` แล้วใช้ `push.sh`
- ถ้ายังอยู่ช่วงทดลอง UI ห้าม run `update_index.py`, ห้าม commit, และห้าม push

---

## AI Import Guard — v6.03

ถ้าใช้ ChatGPT / Claude / AI ตัวอื่นเพื่อช่วยนำเข้าข้อมูล:
- ให้ AI สร้าง **JSON เท่านั้น** อย่าให้แก้ HTML ทั้งไฟล์
- ใช้ `bandsheet_import.py` เป็นตัว validate + sanitize + inject ลง `_template.html`
- หน้า template และทุก song sheet มี `AI import prompt` อยู่ท้ายหน้าให้ copy ไปเริ่ม session ใน AI ตัวอื่น
- ห้ามให้ AI invent chord เอง ใช้ chord chart ที่ user ให้เท่านั้น
- Note/Lyric HTML จะ sanitize เหลือ tag พื้นฐาน: `p`, `br`, `strong`, `b`, `em`, `i`, `u`

ตัวอย่าง:
```bash
python3 bandsheet_import.py song.json --check
python3 bandsheet_import.py song.json --band parkhaus108
python3 bandsheet_import.py song.json --output parkhaus108/song-name.html
```

JSON ที่ AI ควรส่ง:
```json
{
  "title": "Song Title",
  "artist": "Artist",
  "key": "F major",
  "bpm": "96",
  "time": "4/4",
  "vocalist": "",
  "sections": []
}
```

ตัว import guard จะเช็ก:
- marker ใน template ครบ: `END DATA`, `END FOOTER`, `END SETTINGS`
- metadata fields ครบ: `tb-filename`, `tb-artist`, `meta-key`, `meta-bpm`, `meta-time`, `meta-vocalist`
- `sections` เป็น list และ chord section มี `bars`
- note block ต้องเป็น `type: "note"` และมี `cols`
- `rowSizes` ต้องเป็นเลข 1-8
- rhythm ids ต้องอยู่ใน whitelist
- metadata จะ escape ก่อนใส่ HTML attribute

---

## HTML Injection — จุดที่ต้องแก้ (v6.03)

Fields: `tb-filename`, `tb-artist`, `meta-key`, `meta-bpm`, `meta-time`, **`meta-vocalist`** (ใหม่ใน v2.1)

Data markers: `// ── END DATA ──`, `// ── END FOOTER ──`, `// ── END SETTINGS ──`

Python snippet สำหรับ inject (ใช้ swap function เหมือน template):
```python
import json, re

def inject(tmpl, title, artist, key, bpm, time_sig, vocalist, sections_json,
           footer_json='{"notes":[],"links":[]}',
           settings_json='{"chordSize":12.5,"chordFont":"Lato","transpose":0,"noteSize":13}'):
    html = tmpl
    html = html.replace('<title>New Song · Band Sheet</title>', f'<title>{title} · Band Sheet</title>')
    html = re.sub(r'(id="tb-filename"[^>]*value=")[^"]*(")', rf'\g<1>{title}\g<2>', html)
    html = re.sub(r'(id="tb-artist"[^>]*value=")[^"]*(")', rf'\g<1>{artist}\g<2>', html)
    html = re.sub(r'(id="meta-key"[^>]*value=")[^"]*(")', rf'\g<1>{key}\g<2>', html)
    html = re.sub(r'(id="meta-bpm"[^>]*value=")[^"]*(")', rf'\g<1>{bpm}\g<2>', html)
    html = re.sub(r'(id="meta-time"[^>]*value=")[^"]*(")', rf'\g<1>{time_sig}\g<2>', html)
    html = re.sub(r'(id="meta-vocalist"[^>]*value=")[^"]*(")', rf'\g<1>{vocalist}\g<2>', html)
    def swap(html, marker, decl, payload):
        i = html.find(marker)
        if i < 0: return html
        s = html.rfind(decl, 0, i)
        if s < 0: return html
        return html[:s] + decl + payload + ';\n' + html[i:]
    html = swap(html, '// ── END DATA ──',     'var SECTIONS = ', sections_json)
    html = swap(html, '// ── END FOOTER ──',   'var FOOTER = ',   footer_json)
    html = swap(html, '// ── END SETTINGS ──', 'var SETTINGS = ', settings_json)
    return html

with open('_template.html', 'r', encoding='utf-8') as f:
    tmpl = f.read()

html = inject(tmpl, title, f'— {artist}', key, bpm, '4/4', vocalist,
              json.dumps(sections, ensure_ascii=False))

with open(f'{band_folder}/{slug}.html', 'w', encoding='utf-8') as f:
    f.write('<!DOCTYPE html>\n' + html)
```

---

## SECTIONS JSON Format

### Chord Section (ปกติ)
```json
{
  "id": "verse1",
  "label": "Verse 1",
  "note": "optional note text",
  "noteHidden": true,
  "lyric": "",
  "color": {"bar": "#3b82f6", "bg": "#eef4fd", "lbl": "#1e40af"},
  "bars": [
    {"c": "Gm", "a": "", "h": false, "r": ["q","q","q","q"]},
    {"c": "Am7", "a": "", "h": false, "r": []}
  ],
  "rowSizes": [4, 4]
}
```

### Rhythm Strip Fields (v6 prototype)
- `section.rhythmOn: true` — แสดง rhythm strip ทั้ง section
- `bar.r: ["q","ee","rq"]` — rhythm symbols ของ bar นั้น
- `bar.rhythmOff: true` — ซ่อน rhythm strip เฉพาะ bar
- ถ้าไม่ใช้ rhythm ให้ omit field หรือใช้ `r: []`

Rhythm ids ที่รองรับ: `q`, `h`, `dq`, `dh`, `e`, `de`, `ee`, `ssss`, `te`, `rq`, `re`, `rs`

### Lyric Note Block (ใส่เนื้อร้อง)
```json
{
  "id": "note-sec",
  "type": "note",
  "label": "Lyric — Verse 1",
  "cols": ["<p>เนื้อร้อง line 1<br>line 2<br>line 3</p>", ""],
  "color": {"bar": "#3b82f6", "bg": "#eef4fd", "lbl": "#1e40af"}
}
```
ใส่ note block ไว้ **ใต้** chord section ที่เกี่ยวข้องทันที

---

## Chord Notation Rules

| Notation | ความหมาย | ตัวอย่าง |
|---|---|---|
| `Chord` | 1 chord ทั้ง bar | `Gm7` |
| `C1\|C2` | 2 chord ใน 1 bar (beat 1-2 / 3-4) | `Bbmaj7\|F/A` |
| `C1-C2` | passing chord / chromatic | `Abm7-Bb7` |
| `C1/bass` | slash chord | `A/C#`, `G/B` |

---

## Color Palette — Section Types

| Section | bar | bg | lbl |
|---|---|---|---|
| Intro / Outro | `#ff3b30` | `#fff1f0` | `#b00008` |
| Verse | `#3b82f6` | `#eef4fd` | `#1e40af` |
| Pre-Chorus | `#f59e0b` | `#fffbeb` | `#78350f` |
| Chorus | `#ffcc00` | `#fffbe6` | `#7a5e00` |
| Bridge | `#059669` | `#eafaf4` | `#064e3b` |
| Solo / Instrument | `#8b5cf6` | `#f5f3ff` | `#4c1d95` |
| Groove / Vamp | `#ff6b30` | `#fff3ed` | `#8a2e00` |
| Modulation key | `#af52de` | `#f8f0fd` | `#6a2a90` |

---

## rowSizes Rules
- `rowSizes: []` — แสดงทุก bar ใน row เดียว (auto)
- `rowSizes: [4, 4]` — row แรก 4 bars, row ที่สอง 4 bars
- `rowSizes: [7]` — row แรก 7 bars, ที่เหลือ auto
- คิดจากโครงสร้างเพลง: Chorus 2 phrase → `[9, 9]`, Verse 2 สายกีตาร์ → `[4, 7, 7]`

---

## ตัวอย่าง Section Order ทั่วไป

```
Intro → [Lyric block]
Groove/Vamp (ถ้ามี)
Verse 1 → [Lyric block]
Pre-Chorus (ถ้ามี) → [Lyric block]
Chorus → [Lyric block]
Groove/Vamp (ถ้ามี)
Verse 2 → [Lyric block]
Pre-Chorus 2
Chorus 2 → [Lyric block]
Bridge / Solo / Sax Solo
Chorus 3 Final → [Lyric block]
Outro
```

---

## คำสั่งที่รองรับ

```bash
# สร้าง bandsheet ใหม่
Codex "สร้าง bandsheet เพลง {ชื่อเพลง} — {ศิลปิน}"

# rebuild จาก chord ใหม่ที่ user ให้มา
Codex "rebuild {filename}.html จาก chord นี้: [chord text]"

# แก้เฉพาะ section
Codex "แก้ Chorus ใน {filename}.html เป็น [chord ใหม่]"
```

---

## ข้อควรระวัง
- **ห้ามหา chord จาก web** — ผิดพลาดได้ง่าย user จะให้มาเอง
- **อย่าแก้ `_template.html` โดยตรงเพื่อสร้างเพลง** — ใช้ inject แล้ว write ไปยัง path ใหม่
- **ถ้า update template** (เพิ่ม feature, เปลี่ยน layout) — backup ก่อน แล้ว update ทุก song file พร้อมกัน
- **ตรวจ marker** `// ── END DATA ──`, `// ── END FOOTER ──`, `// ── END SETTINGS ──` ก่อน inject
- Lyric note block ต้องใช้ `"type": "note"` — ถ้าไม่มี field นี้จะ render เป็น chord section แทน
- Song files อัพโหลดผ่าน ⬆ Upload button (เปิด github.com/tikittisak/bandsheet) — drag & drop ขึ้น GitHub

---

## GitHub Auto-Push Workflow (ใหม่)

### หลัง save/แก้ไฟล์ ให้ run:
```bash
osascript -e 'do shell script "cd /Users/ti_am1/Desktop/Vaults/Vault_ti.muse/Bandsheet && bash push.sh 2>&1" '
```
หรือถ้าต้องการใส่ commit message เอง:
```bash
osascript -e 'do shell script "cd /Users/ti_am1/Desktop/Vaults/Vault_ti.muse/Bandsheet && bash push.sh \"add: song-name.html\" 2>&1" '
```

### push.sh จะทำ:
1. `python3 update_index.py` — อัพเดต SONGS array ในทุก band/index.html อัตโนมัติ
2. `git add -A` — stage ไฟล์ทั้งหมด
3. `git commit -m "..."` — commit
4. `git push origin main` — push ไป github.com/tikittisak/bandsheet

### Bandsheet Folder Path (ถูกต้อง):
```
/Users/ti_am1/Desktop/Vaults/Vault_ti.muse/Bandsheet/
```

### คำสั่ง write ไฟล์ใน Cowork (ต้องใช้ osascript):
```python
# ใช้ osascript เพื่อเขียนไฟล์ไปยัง Vault path
do shell script "python3 -c '...' > /Users/ti_am1/Desktop/Vaults/Vault_ti.muse/Bandsheet/{band}/{song}.html"
```
