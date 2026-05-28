# Bandsheet v6.04 Design Language Manual

เอกสารนี้เป็น source of truth สำหรับออกแบบและสร้าง app ใหม่ในแนวทางเดียวกับ Bandsheet v6.04 โดยยึด `_template.html` v6.04 เป็น baseline ที่ใช้งานจริง ไม่ใช่การออกแบบจากศูนย์

## File Decision

ใช้ `DESIGN_LANGUAGE.md` เป็นไฟล์หลัก เพราะเหมาะกับการทำงานของโปรเจกต์นี้ที่สุด:

- อ่านง่ายใน repo และเปิดดูได้โดยไม่ต้องรัน app
- diff / review / version control ง่ายกว่า HTML
- ใส่ design tokens, checklist, JSON contract, HTML/CSS snippets และ prompt instructions ได้ในไฟล์เดียว
- เหมาะเป็นเอกสารตั้งต้นให้ AI/Codex builder ใช้สร้าง project ใหม่

ไม่ใช้ `.html` เป็น source of truth หลัก เพราะดูแล version ยากกว่าและมักกลายเป็น demo แทน guideline จริง หากต้องการ visual demo ในอนาคต ให้สร้างเป็น companion file แยกจากเอกสารนี้

## Product Concept

Bandsheet v6.04 คือ working surface สำหรับนักดนตรีและคนจัด chord chart ไม่ใช่ landing page หรือ document viewer ธรรมดา เป้าหมายคือทำให้ rehearsal อ่านเร็ว แก้เร็ว และ export ได้ทันที

หลักคิดสำคัญ:

- **Rehearsal-first**: หน้าจอหลักต้องอ่าน chord ได้เร็วระหว่างซ้อม ลดสิ่งรบกวนให้มากที่สุด
- **Compact editor**: เครื่องมือแก้ไขต้องอยู่ใกล้งาน แต่ซ่อนความซับซ้อนจนกว่าจะเข้า edit mode
- **Readable band sheet**: cell, section, color, repeat, rhythm และ note ต้อง scan ได้ในจังหวะสายตาเดียว
- **Fast edit/export**: แก้ metadata, transpose, font size, section order, row size, rhythm และ export JPG/HTML ได้จากหน้าเดียว
- **Data-driven template**: UI render จาก `SECTIONS`, `FOOTER`, `SETTINGS`; song file คือ template shell + injected data

## UX Model

โครงสร้างหน้า v6.04 แบ่งเป็น 4 ชั้น:

1. **Toolbar**: sticky utility bar สำหรับ mode, view, font, size, transpose, save/export และ AI prompt
2. **Metabar**: metadata row สำหรับ title, artist, key, bpm, time, vocalist
3. **Sheet canvas**: working area ที่ render section, row, bar cell, lyric/note block และ repeat badge
4. **Footer notes**: note ท้ายเพลงสำหรับ performance detail หรือ band reminder

Default state คือ `body.view-mini` เพราะเป็น performance chart view ที่อ่านเร็วที่สุด:

- bar cell สูง 44px
- gap ระหว่าง bar เป็น 0px
- cell ต่อกันแบบ chart strip
- annotation ถูกซ่อนใน mini view
- tool controls ที่ไม่จำเป็นถูกซ่อนนอก edit mode

Edit mode ไม่ควรเปลี่ยนบุคลิกของ app ให้รก แต่ควรเปิดเผย affordance เพิ่มเฉพาะจุด เช่น add row, duplicate, reorder, delete, rhythm toggle, color picker และ rich text toolbar

## Visual Principles

- **Dense but calm**: ข้อมูลแน่นได้ แต่ contrast ต้องนิ่งและไม่ตะโกน
- **Utility, not marketing**: ห้ามทำ hero, card-heavy landing, decorative illustration หรือ layout ที่เหมือน product website
- **Color as navigation**: สี section ใช้บอกชนิดของท่อนเพลงและช่วย scan ไม่ใช่ decoration
- **Low chrome**: toolbar และ controls ใช้สีเทาอ่อน เส้นบาง hover เบา และ active state ชัดพอดี
- **Small radius by purpose**: mini chart cell ใช้ 1px, controls ใช้ 3-6px, popup ใช้ 8-10px
- **Thin borders, minimal shadows**: shadow ใช้เฉพาะ hover, popup, drag feedback เท่านั้น
- **Text hierarchy is compact**: section label 9px uppercase, chord 13px mini, meta/control 12px, note 13px line-height 1.65-1.7
- **No nested card feel**: sheet section ไม่เป็น floating card; card ใช้เฉพาะ repeated note/footer items หรือ popup

## Design Tokens

Tokens ต่อไปนี้มาจาก `_template.html` v6.04 และควรเป็น baseline ของ project ใหม่

```css
:root {
  --bg: #f7f9fc;
  --surface: #fff;
  --border: #dfe7f2;
  --border-strong: #c8d4e3;
  --text: #172033;
  --text-muted: #7d8ca0;
  --text-faint: #b7c3d1;
  --accent: #334155;

  --ui-ink: #5f6f83;
  --ui-muted: #9aa8ba;
  --ui-line: #e6edf5;
  --ui-soft: #f3f7fb;
  --ui-hover: #edf3f9;
  --ui-active: #60758d;

  --cell-w: 164px;
  --cell-h: 64px;
  --gap: 6px;
  --radius: 5px;

  --chord-font: 'Roboto Condensed';
  --note-font: 'IBM Plex Sans Thai Looped', sans-serif;
}

body.view-mini {
  --cell-h: 44px;
  --gap: 0px;
}
```

Font roles:

- system UI font: toolbar, metabar, labels, bar numbers, export header
- `Roboto Condensed`: default chord font
- `Roboto Condensed`, `Roboto Mono`, `Petaluma`: selectable chord fonts
- `IBM Plex Sans Thai`: page/body Thai UI
- `IBM Plex Sans Thai Looped`: lyric/note content

Section color presets:

```css
/* Use as semantic section colors, not decoration */
.section-intro  { --bar: #ff3b30; --bg: #fff1f0; --lbl: #b00008; }
.section-verse  { --bar: #3b82f6; --bg: #eef4fd; --lbl: #1e40af; }
.section-pre    { --bar: #f59e0b; --bg: #fffbeb; --lbl: #78350f; }
.section-chorus { --bar: #ffcc00; --bg: #fffbe6; --lbl: #7a5e00; }
.section-bridge { --bar: #059669; --bg: #eafaf4; --lbl: #064e3b; }
.section-solo   { --bar: #8b5cf6; --bg: #f5f3ff; --lbl: #4c1d95; }
.section-vamp   { --bar: #ff6b30; --bg: #fff3ed; --lbl: #8a2e00; }
.section-mod    { --bar: #af52de; --bg: #f8f0fd; --lbl: #6a2a90; }
```

## Component Specs

### Toolbar

Purpose: command surface ที่อยู่ติดบนสุด แต่ไม่แย่ง attention จาก chord chart

- Sticky top, white translucent surface, subtle blur, 1px bottom border
- Height ของ controls ประมาณ 26-27px
- Button text lowercase ยกเว้น symbol controls
- Group separator ใช้เส้นแนวตั้งบาง ไม่ใช้ card หรือ panel
- Active state ใช้ `--ui-active` + text ขาว
- Ghost export actions ใช้ muted text จน hover

### Metabar

Purpose: metadata ที่แก้ได้ทันทีและ export ไปกับ song

- อยู่ใต้ toolbar เป็นแถบเรียบ
- input เป็น soft pill เล็ก ไม่เหมือน form หนัก
- fields หลัก: `tb-filename`, `tb-artist`, `meta-key`, `meta-bpm`, `meta-time`, `meta-vocalist`
- separator ใช้ `·` และ label lowercase

### Section Head

Purpose: scan จุดเริ่มของท่อนเพลงอย่างรวดเร็ว

- `.section-tag` ใช้ uppercase, 9px, letter-spacing `.1em`
- tag background ใช้ section `bg`, text ใช้ `lbl`, border ใช้ `bar` แบบ alpha
- note toggle เป็น affordance เบา ซ่อน section note เมื่อไม่จำเป็น
- edit actions วางขวาและซ่อนใน view mode

### Bar Cell

Purpose: แสดง 1 ห้องเพลงอย่างประหยัดพื้นที่

- Normal cell: border 1px, radius 5px, white surface
- Mini cell: border none, radius 1px, `box-shadow: inset 2px 0 0 var(--bar-accent)`
- Top strip ใน mini view สูง 12px ใช้สี section แบบอ่อน
- Bar number อยู่บนซ้าย 8px ใน mini view
- Special note อยู่บนขวา 7px ใน mini view
- Chord ใช้ 13px, weight 500, line-height 1 ใน mini view
- Annotation ซ่อนใน mini view
- Highlight ใช้ background เข้มจาก section color และ text ขาว

### Lyric / Note Section

Purpose: ใส่เนื้อร้องหรือ performance note ใต้ chord section โดยตรง

- ใช้ `type: "note"` ใน data เท่านั้น
- รองรับ 1-2 columns
- content ใช้ note font, 13px, line-height 1.65-1.7
- left border 3px ใช้ section color
- background white, radius เฉพาะด้านขวา
- edit mode แสดง rich text toolbar แบบเล็ก

### Rhythm Picker

Purpose: เพิ่ม rhythm strip ต่อ bar โดยไม่ทำให้ chord chart หลักรก

- Rhythm strip อยู่เหนือ bar cell เฉพาะ bar ที่เปิด rhythm
- Picker เป็น popup 380px, radius 10px, shadow ชัดกว่าส่วนอื่น
- Grid 4 columns, item สูงประมาณ 58px
- Selected state ใช้พื้นดำและ invert icon
- Clear action ต้องเห็นง่ายแต่ไม่เด่นกว่า rhythm choices

### Export Style

Purpose: สร้าง JPG ที่สะอาดกว่า edit surface แต่ยังคง DNA เดิม

- Export width baseline 1120px
- Export cell width baseline 128px
- ใช้ background `#f7f9fc`
- Header ใช้ system UI font, title 24px, artist 14px, meta 13px
- Bar cell export ใช้ radius 1px, no border, left inset accent, top strip
- Note export ใช้ width เท่ากับ chart row ที่กว้างสุด

## Data Contract

Project ใหม่ที่ใช้หลักการเดียวกันควรแยก template shell ออกจาก song data:

```js
var SECTIONS = [
  {
    id: "verse1",
    label: "Verse 1",
    note: "",
    noteHidden: true,
    lyric: "",
    color: { bar: "#3b82f6", bg: "#eef4fd", lbl: "#1e40af" },
    bars: [
      { c: "Gm", a: "", h: false, r: [] },
      { c: "Bbmaj7|F/A", a: "", h: false, r: ["q", "q", "q", "q"] }
    ],
    rowSizes: [4, 4]
  },
  {
    id: "lyric-verse1",
    type: "note",
    label: "Lyric - Verse 1",
    cols: ["<p>line 1<br>line 2</p>", ""],
    color: { bar: "#3b82f6", bg: "#eef4fd", lbl: "#1e40af" }
  }
];

var FOOTER = { notes: [] };
var SETTINGS = {
  chordSize: 12.5,
  chordFont: "Roboto Condensed",
  transpose: 0,
  noteSize: 13
};
```

AI import rule:

- AI ต้องส่ง JSON เท่านั้น
- ห้ามให้ AI แก้ HTML ทั้งไฟล์
- ห้ามให้ AI invent chord จาก web
- ใช้ chord chart จาก user เท่านั้น
- Validate/sanitize ผ่าน `bandsheet_import.py`
- Note HTML อนุญาตเฉพาะ tag พื้นฐาน: `p`, `br`, `strong`, `b`, `em`, `i`, `u`

## HTML-to-Figma Copy Guide

ใช้ snippets ต่อไปนี้เป็น static HTML/CSS สำหรับ paste/inspect ใน Figma หรือใช้เป็น visual reference ไม่ต้องพึ่ง JavaScript

### Static Token Block

```html
<style>
  :root {
    --bg: #f7f9fc;
    --surface: #fff;
    --border: #dfe7f2;
    --border-strong: #c8d4e3;
    --text: #172033;
    --text-muted: #7d8ca0;
    --text-faint: #b7c3d1;
    --ui-ink: #5f6f83;
    --ui-muted: #9aa8ba;
    --ui-line: #e6edf5;
    --ui-soft: #f3f7fb;
    --ui-hover: #edf3f9;
    --ui-active: #60758d;
    --bar: #3b82f6;
    --bar-bg: #eef4fd;
    --bar-label: #1e40af;
    --cell-w: 128px;
    --cell-h: 44px;
  }

  body {
    margin: 0;
    background: var(--bg);
    color: var(--text);
    font-family: 'IBM Plex Sans Thai', sans-serif;
  }
</style>
```

### Minimal Screen Skeleton

```html
<main class="bandsheet-static">
  <div class="toolbar">
    <div class="tb-group">
      <button>&lt;</button>
      <button class="active">edit</button>
    </div>
    <div class="tb-group">
      <span>view</span>
      <button>chord</button>
      <button>note</button>
    </div>
    <div class="tb-group">
      <button>A-</button>
      <span class="seg-val">12.5</span>
      <button>A+</button>
    </div>
    <div class="brand">bandsheet by ti.muse <span>v6.04</span></div>
  </div>

  <div class="metabar">
    <span class="title">Song Title</span>
    <span class="artist">- Artist</span>
    <span>key</span><strong>F major</strong>
    <span>bpm</span><strong>96</strong>
    <span>time</span><strong>4/4</strong>
  </div>

  <section class="sheet">
    <div class="section-head">
      <span class="section-tag">Verse 1</span>
    </div>
    <div class="bar-row">
      <div class="bar-cell"><span class="num">1</span><strong>F</strong></div>
      <div class="bar-cell"><span class="num">2</span><strong>Dm7</strong></div>
      <div class="bar-cell"><span class="num">3</span><strong>Gm7</strong></div>
      <div class="bar-cell"><span class="num">4</span><strong>C7</strong></div>
    </div>
    <div class="note-block">Lyric or band note line 1<br>line 2</div>
  </section>
</main>
```

### Static Component CSS

```html
<style>
  .toolbar {
    min-height: 36px;
    padding: 4px 14px;
    display: flex;
    align-items: center;
    gap: 8px;
    border-bottom: 1px solid var(--ui-line);
    background: rgba(255, 255, 255, 0.97);
    font-family: var(--ui-font);
    font-size: 12px;
  }

  .tb-group {
    display: flex;
    align-items: center;
    gap: 3px;
    padding-left: 8px;
    border-left: 1px solid var(--ui-line);
  }

  .tb-group:first-child {
    border-left: 0;
    padding-left: 0;
  }

  button {
    height: 27px;
    padding: 4px 8px;
    border: 0;
    border-radius: 6px;
    background: transparent;
    color: var(--ui-ink);
    font: inherit;
    text-transform: lowercase;
  }

  button.active {
    background: var(--ui-active);
    color: #f8fbff;
  }

  .seg-val {
    min-width: 29px;
    padding: 0 7px;
    color: var(--ui-muted);
    border-left: 1px solid var(--ui-line);
    border-right: 1px solid var(--ui-line);
    text-align: center;
  }

  .brand {
    margin-left: auto;
    color: var(--ui-muted);
  }

  .brand span {
    font-weight: 300;
  }

  .metabar {
    padding: 6px 24px;
    display: flex;
    align-items: center;
    gap: 8px;
    border-bottom: 1px solid var(--border);
    background: var(--surface);
    color: var(--ui-muted);
    font: 12px var(--ui-font);
  }

  .metabar strong {
    color: var(--ui-ink);
    font-weight: 400;
  }

  .sheet {
    width: min(100%, 1120px);
    margin: 0 auto;
    padding: 8px 24px 24px;
  }

  .section-head {
    margin-bottom: 4px;
  }

  .section-tag {
    display: inline-block;
    padding: 2px 8px;
    border: 1px solid color-mix(in srgb, var(--bar) 27%, transparent);
    border-radius: 3px;
    background: var(--bar-bg);
    color: var(--bar-label);
    font: 700 9px var(--ui-font);
    letter-spacing: .1em;
    text-transform: uppercase;
  }

  .bar-row {
    display: flex;
    gap: 0;
    align-items: flex-end;
    margin-bottom: 4px;
  }

  .bar-cell {
    position: relative;
    width: var(--cell-w);
    min-height: var(--cell-h);
    padding: 17px 6px 7px 7px;
    overflow: hidden;
    border-radius: 1px;
    background: var(--bar-bg);
    box-shadow: inset 2px 0 0 var(--bar);
  }

  .bar-cell::before {
    content: "";
    position: absolute;
    inset: 0 0 auto;
    height: 12px;
    background: color-mix(in srgb, var(--bar) 28%, white);
    opacity: .72;
  }

  .bar-cell .num {
    position: absolute;
    top: 2px;
    left: 6px;
    z-index: 1;
    color: var(--bar-label);
    font: 600 8px/8px var(--ui-font);
  }

  .bar-cell strong {
    display: block;
    color: var(--text);
    font: 500 13px/1.05 Roboto Condensed, sans-serif;
    overflow-wrap: normal;
  }

  .note-block {
    margin-top: 8px;
    padding: 9px 11px;
    border-left: 3px solid var(--bar);
    border-radius: 0 5px 5px 0;
    background: var(--surface);
    color: var(--text);
    font: 400 13px/1.7 'IBM Plex Sans Thai Looped', sans-serif;
  }
</style>
```

Figma mapping:

- CSS variables -> Figma variables
- `.toolbar`, `.tb-group`, `button`, `.seg-val` -> toolbar component set
- `.metabar` -> metadata component
- `.section-tag` -> section label component with color variants
- `.bar-cell` -> mini bar cell component
- `.note-block` -> lyric/note component
- Section color presets -> semantic color styles such as Intro, Verse, Chorus, Bridge, Solo

## Builder Checklist

ใช้ checklist นี้เมื่อสร้าง project ใหม่จากหลักการ v6.04:

- หน้าแรกต้องเป็น usable working surface ไม่ใช่ marketing page
- กำหนด data model ก่อน UI detail: sections, items/bars, notes, settings
- สร้าง view mode ที่อ่านเร็วที่สุดเป็น default
- ซ่อน editing controls จนกว่าจะเข้า edit mode
- ใช้ semantic color เพื่อช่วย scan structure
- ทำ metadata เป็น editable inline row
- ทำ export style แยกจาก edit surface แต่ใช้ visual DNA เดียวกัน
- ถ้ามี AI import ให้ AI ส่ง structured JSON และ validate ก่อน inject
- ห้ามให้ AI แตะ template ทั้งไฟล์เมื่อแค่นำเข้าข้อมูล
- ก่อน sync template/layout ไป instance files ต้องให้ user confirm design/behavior ก่อน

## Lessons Learned

- อย่าเริ่มจากหน้าเปล่า ให้เริ่มจาก v6.04 behavior ที่พิสูจน์แล้ว: toolbar, metabar, mini sheet, edit mode, export
- ความเร็วในการอ่านสำคัญกว่าความสวยแบบ showcase
- ความแน่นของข้อมูลใช้ได้ ถ้า hierarchy, color และ spacing คุมดี
- Section color ต้องช่วยจำตำแหน่งในเพลง ไม่ควรกลายเป็น palette โชว์
- Mini view ต้องมาก่อน full editor view เพราะวงดนตรีใช้ตอนเล่นจริง
- UI controls ควรเป็นคำสั้นหรือ symbol ที่ scan ได้ ไม่ต้องมีคำอธิบายในหน้า
- Rich editing ควรอยู่ใน context ของ content ไม่แยกเป็น admin screen
- Export ไม่ควรถ่ายหน้าจอดิบ ต้อง render clean sheet ที่ตัด controls ออก
- Template คือ runtime shell; song data คือ payload
- Guardrails สำคัญมาก: validate markers, metadata fields, note HTML และ rhythm ids ทุกครั้ง

## Non-Goals

- ไม่ทำ landing page
- ไม่ใช้ decorative backgrounds, gradient blobs, oversized hero หรือ card-heavy layout
- ไม่ออกแบบให้เป็น document editor ทั่วไป
- ไม่ให้ web search หา chord
- ไม่ให้ AI invent chord หรือแก้ HTML ทั้งไฟล์เพื่อ import เพลง
- ไม่ sync template changes ไป song files ระหว่าง UI review
