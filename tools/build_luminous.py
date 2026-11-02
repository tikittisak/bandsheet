#!/usr/bin/env python3
"""Build a hardened trial UI from the immutable alpha.1 Git reference.

Never imports or migrates a song. Embedded musical payloads must match exactly.
"""
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]
REF = "4fb98e91389ddc021dea13996d9a72a7ed11ae75"
SOURCE = "_archive/prototypes/preview-resistance-luminous-mobile-test.html"
OUTPUT = ROOT / "_archive/prototypes/preview-luminous-v7.0.0-alpha.2.html"


def preview_html():
    original = subprocess.check_output(["git", "show", f"{REF}:{SOURCE}"], cwd=ROOT).decode()
    if hashlib.sha256(original.encode()).hexdigest() != "b5f41bda0c5cc8c87b04a0bc322559ae5b84ce27041e800a201eefb449584bc5":
        raise ValueError("pinned source hash mismatch")
    doc = original
    # The frozen baseline still contains a retired AI-import clipboard prompt.
    # Alpha.2 must not carry that suspended workflow, even as unreachable code.
    legacy_prompt_start = '\nvar AI_START_PROMPT = ['
    legacy_prompt_end = '\nfunction makeFooterCtrl('
    if doc.count(legacy_prompt_start) != 1 or doc.count(legacy_prompt_end) != 1:
        raise ValueError('legacy AI prompt removal anchor changed')
    prompt_start = doc.index(legacy_prompt_start)
    prompt_end = doc.index(legacy_prompt_end, prompt_start)
    doc = doc[:prompt_start] + '\n' + doc[prompt_end:]

    # Do not intercept native rich-text shortcuts. Safari can leave the caret's
    # typing state stuck after the deprecated execCommand('bold') path. Native
    # contenteditable Cmd/Ctrl+B toggles both on and off and emits input when
    # the user types, which the existing editor persistence already observes.
    legacy_shortcut_start = '\nfunction richTextShortcut(e){'
    legacy_shortcut_end = '\nfunction baseRowsFor('
    if doc.count(legacy_shortcut_start) != 1 or doc.count(legacy_shortcut_end) != 1:
        raise ValueError('legacy rich-text shortcut removal anchor changed')
    shortcut_start = doc.index(legacy_shortcut_start)
    shortcut_end = doc.index(legacy_shortcut_end, shortcut_start)
    doc = doc[:shortcut_start] + '\n' + doc[shortcut_end:]
    shortcut_binding = "        ed.addEventListener('keydown',richTextShortcut);\n"
    if doc.count(shortcut_binding) != 1:
        raise ValueError('legacy rich-text shortcut binding anchor changed')
    doc = doc.replace(shortcut_binding, '', 1)
    old = "html=html.slice(0,s)+decl+json+';\\n'+html.slice(i);"
    new = "html=html.slice(0,s)+decl+json.replace(/</g,'\\\\u003c')+';\\n'+html.slice(i);"
    if doc.count(old) != 1:
        raise ValueError("export serialization anchor changed")
    doc = doc.replace(old, new)
    doc = doc.replace("  SETTINGS.chordFont = CONTENT_FONT;", "  // Typography is view-only; preserve SETTINGS.chordFont.")
    doc = doc.replace("Resistance · Muse · 80/20 Prototype", "Resistance · Luminous v7.0.0-alpha.2")
    # The filename/title input is user text, never markup.
    title_line = next(line for line in doc.splitlines() if "html=html.replace(/<title>" in line and "'<title>'+fn" in line)
    doc = doc.replace(title_line,
        "  html=html.replace(/<title>[^<]*<\\/title>/,function(){return '<title>'+auditEscape(fn+(ar?' '+ar:''))+' · bandsheet</title>'});")
    doc = doc.replace("function saveToFile(){", "function auditEscape(value){return String(value).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;')}\nfunction saveToFile(){")
    doc = doc.replace("dirty?'unsaved changes':'saved'", "dirty?'unsaved changes':'loaded / export requested'")
    doc = doc.replace("'บันทึกแล้ว · revision '", "'ส่งออก HTML · ตรวจไฟล์ใน Downloads · revision '")
    # Runtime #sheet acquires a style attribute, so the old exact opening-tag
    # pattern failed to clear it. Serialized focus buttons race parser startup.
    sheet_pattern = r'/<div id="sheet">[\s\S]*?'
    if doc.count(sheet_pattern) != 1:
        raise ValueError('runtime sheet cleanup anchor changed')
    doc = doc.replace(sheet_pattern, r'/<div id="sheet"[^>]*>[\s\S]*?', 1)
    cleanup_start = 'function cleanRuntimeHtml(html){'
    doc = doc.replace(cleanup_start, cleanup_start + '''
  html=html.replace(/<button\\b[^>]*id="focus-return"[^>]*>[\\s\\S]*?<\\/button>/g,'');''', 1)
    # outerHTML preserves the runtime button, but not its onclick property.
    # Rebind an exported button as well as a newly created one on startup.
    focus_start = doc.index('  function ensureFocusReturn() {')
    focus_end = doc.index('\n  function renderFocusAnchor()', focus_start)
    doc = doc[:focus_start] + '''  function ensureFocusReturn() {
    var button = document.getElementById('focus-return');
    if (!button) {
      button = document.createElement('button');
      button.id = 'focus-return';
      button.className = 'focus-return';
      button.type = 'button';
      document.body.appendChild(button);
    }
    button.onclick = function () { window.returnToFocus(); };
    return button;
  }
''' + doc[focus_end:]
    # P0 patches apply to a derived alpha.2 document, never the frozen source.
    viewport = '<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0">'
    if doc.count(viewport) != 1:
        raise ValueError('viewport anchor changed')
    doc = doc.replace(viewport, '<meta name="viewport" content="width=device-width, initial-scale=1">')
    resize_start = doc.index('var LAST_VISUAL_CAP=currentVisualCap();')
    resize_end = doc.index('\nfunction render(){', resize_start)
    layout = Path(__file__).with_name('luminous_layout.js').read_text(encoding='utf-8')
    doc = doc[:resize_start] + layout + '\nfunction render(){return renderData();}\n' + doc[resize_end:]
    doc = doc.replace('function render(){\n  var keepY=', 'function renderData(){\n  var keepY=', 1)
    doc = doc.replace('function updateCellWidth(){',
                      'function updateCellWidth(){updateLayout();}\nfunction updateCellWidthCore(){', 1)
    doc = doc.replace("window.addEventListener('resize', syncPairOffsets, { passive: true });",
                      "document.addEventListener('bandsheet:layout', syncPairOffsets);")
    css = '''<style id="luminous-layout-p0">
/* Geometry only. Existing bar nodes wrap without rebuilding data rows. */
body:not(.edit-mode) .bar-row-main { flex: 0 1 auto; flex-wrap: wrap; max-width: 100%; }
</style>'''
    doc = doc.replace('</head>', css+'\n</head>', 1)

    # Alpha.2 UI: one role-based performance switch at every breakpoint.
    old_switch = '''  <div class="tb-group mobile-view-switch" aria-label="Mobile view">
    <div class="seg-ctrl">
      <button class="seg-btn active" id="band-view-btn" onclick="setMobileView('band')">band</button>
      <button class="seg-btn" id="lyric-view-btn" onclick="setMobileView('lyric')">lyric</button>
    </div>
  </div>'''
    new_switch = '''  <div class="tb-group performance-view-switch" aria-label="Performance view">
    <div class="seg-ctrl">
      <button class="seg-btn" id="band-view-btn" onclick="setPerformanceView('band')">band</button>
      <button class="seg-btn" id="vocal-view-btn" onclick="setPerformanceView('vocal')">vocal</button>
    </div>
  </div>'''
    if doc.count(old_switch) != 1:
        raise ValueError('performance switch anchor changed')
    doc = doc.replace(old_switch, new_switch, 1)

    # Bar numbers remain off by default, but performers may reveal them in
    # Display mode without changing song data or persisted settings.
    readability_end = '''    <div class="seg-ctrl" title="Lyric and note size">
      <button class="seg-btn" onclick="changeNoteSize(-1)">n−</button>
      <span class="seg-val" id="note-size-val">16</span>
      <button class="seg-btn" onclick="changeNoteSize(1)">n+</button>
    </div>
  </div>'''
    readability_with_bar_numbers = '''    <div class="seg-ctrl" title="Lyric and note size">
      <button class="seg-btn" onclick="changeNoteSize(-1)">n−</button>
      <span class="seg-val" id="note-size-val">16</span>
      <button class="seg-btn" onclick="changeNoteSize(1)">n+</button>
    </div>
    <button class="tb-btn bar-number-toggle" id="bar-number-btn" type="button"
      onclick="toggleBarNumbers()" aria-pressed="false" title="Show or hide bar numbers">bar no.</button>
  </div>'''
    if doc.count(readability_end) != 1:
        raise ValueError('readability toolbar anchor changed')
    doc = doc.replace(readability_end, readability_with_bar_numbers, 1)

    # The inline section-label editor must use the same mapped Luminous tone as
    # its rendered heading. Reading the rendered tag avoids a second color path.
    raw_editor_color = "inp.style.background=(SECTIONS[idx].color||{}).bg||'#eef';inp.style.color=(SECTIONS[idx].color||{}).lbl||'#333';inp.style.borderColor=(SECTIONS[idx].color||{}).bar||'#888';"
    mapped_editor_color = "var renderedTone=getComputedStyle(el);inp.style.background=renderedTone.backgroundColor;inp.style.color=renderedTone.color;inp.style.borderColor=renderedTone.borderLeftColor;"
    if doc.count(raw_editor_color) != 1:
        raise ValueError('section editor color anchor changed')
    doc = doc.replace(raw_editor_color, mapped_editor_color, 1)

    # Rename the legacy mobile-only state and expose role view on desktop too.
    replacements = (
        # Replace the longer selectors before the shared class token.
        ("body:not(.edit-mode) .mobile-view-switch { display: flex; }", "body:not(.edit-mode) .performance-view-switch { display: flex; }"),
        ("body.edit-mode .mobile-view-switch { display: none; }", "body.edit-mode .performance-view-switch { display: none; }"),
        ('.mobile-view-switch { display: none; }', '.performance-view-switch { display: flex; }\n  body.edit-mode .performance-view-switch { display: none; }'),
        ('.mobile-view-switch .seg-btn.active', '.performance-view-switch .seg-btn.active'),
        ("document.body.classList.contains('mobile-lyric')", "document.body.classList.contains('view-vocal')"),
    )
    for old, new in replacements:
        if old not in doc:
            raise ValueError(f'UI state anchor changed: {old}')
        doc = doc.replace(old, new)

    old_view_state = '''  var MOBILE_VIEW = 'lyric';
  window.setMobileView = function (mode) {
    var nextView = mode === 'lyric' ? 'lyric' : 'band';
    if (nextView !== MOBILE_VIEW) closeChordPeeks();
    MOBILE_VIEW = nextView;
    document.body.classList.toggle('mobile-band', MOBILE_VIEW === 'band');
    document.body.classList.toggle('mobile-lyric', MOBILE_VIEW === 'lyric');
    var band = document.getElementById('band-view-btn');
    var lyric = document.getElementById('lyric-view-btn');
    if (band) band.classList.toggle('active', MOBILE_VIEW === 'band');
    if (lyric) lyric.classList.toggle('active', MOBILE_VIEW === 'lyric');
  };'''
    new_view_state = '''  var PERFORMANCE_VIEW = window.matchMedia('(max-width: 760px)').matches ? 'vocal' : 'band';
  window.setPerformanceView = function (mode) {
    var nextView = mode === 'vocal' ? 'vocal' : 'band';
    if (nextView !== PERFORMANCE_VIEW) closeChordPeeks();
    PERFORMANCE_VIEW = nextView;
    document.body.classList.toggle('view-band', PERFORMANCE_VIEW === 'band');
    document.body.classList.toggle('view-vocal', PERFORMANCE_VIEW === 'vocal');
    document.body.dataset.performanceView = PERFORMANCE_VIEW;
    var band = document.getElementById('band-view-btn');
    var vocal = document.getElementById('vocal-view-btn');
    if (band) band.classList.toggle('active', PERFORMANCE_VIEW === 'band');
    if (vocal) vocal.classList.toggle('active', PERFORMANCE_VIEW === 'vocal');
    requestAnimationFrame(syncPairOffsets);
  };'''
    if doc.count(old_view_state) != 1:
        raise ValueError('performance view state anchor changed')
    doc = doc.replace(old_view_state, new_view_state, 1)
    # Remaining legacy role names are CSS class selectors. Do this only after
    # replacing the JavaScript state block so its exact anchor stays auditable.
    doc = doc.replace('.mobile-band', '.view-band')
    doc = doc.replace('.mobile-lyric', '.view-vocal')
    doc = doc.replace('window.setMobileView(MOBILE_VIEW);', 'window.setPerformanceView(PERFORMANCE_VIEW);')

    bar_number_state = '''  var BAR_NUMBERS_VISIBLE = false;
  window.toggleBarNumbers = function () {
    BAR_NUMBERS_VISIBLE = !BAR_NUMBERS_VISIBLE;
    document.body.classList.toggle('show-bar-numbers', BAR_NUMBERS_VISIBLE);
    var button = document.getElementById('bar-number-btn');
    if (button) {
      button.classList.toggle('active', BAR_NUMBERS_VISIBLE);
      button.setAttribute('aria-pressed', BAR_NUMBERS_VISIBLE ? 'true' : 'false');
    }
  };

'''
    if doc.count('  var PERFORMANCE_VIEW = ') != 1:
        raise ValueError('bar-number state insertion anchor changed')
    doc = doc.replace('  var PERFORMANCE_VIEW = ', bar_number_state + '  var PERFORMANCE_VIEW = ', 1)

    # Wide defaults improve readability on an external display without
    # stretching the working surface across the full viewport.
    default_sizes = "  CHORD_SIZE = 15;\n  NOTE_SIZE = 16;"
    wide_sizes = "  var WIDE_DISPLAY = window.matchMedia('(min-width: 1440px)').matches;\n  CHORD_SIZE = WIDE_DISPLAY ? 17 : 15;\n  NOTE_SIZE = WIDE_DISPLAY ? 17 : 16;"
    if doc.count(default_sizes) != 1:
        raise ValueError('typography default anchor changed')
    doc = doc.replace(default_sizes, wide_sizes, 1)

    # Bar numbers are navigational metadata, not row emphasis. The first bar
    # and highlighted bar therefore use the same quiet typography as all bars.
    first_bar_number = '''  body.view-mini .bar-row-main .bar-col:first-child .bar-num {
    color: var(--bar-number-strong) !important;
    font-weight: 500 !important;
  }'''
    highlighted_bar_number = '''  body.view-mini .bar-row-main .bar-col .bar-cell.highlighted .bar-num {
    color: #5873a5 !important;
    font-weight: 500 !important;
  }'''
    if doc.count(first_bar_number) != 1 or doc.count(highlighted_bar_number) != 1:
        raise ValueError('bar-number typography anchor changed')
    doc = doc.replace(first_bar_number + '\n', '', 1)
    doc = doc.replace(highlighted_bar_number + '\n', '', 1)
    legacy_highlight_group = '.bar-cell.highlighted,.bar-cell.highlighted .bar-num,.bar-cell.highlighted .bar-snote,.bar-cell.highlighted .bar-chord,.bar-cell.highlighted .bar-chord-part,.bar-cell.highlighted .bar-ann'
    neutral_highlight_group = '.bar-cell.highlighted,.bar-cell.highlighted .bar-snote,.bar-cell.highlighted .bar-chord,.bar-cell.highlighted .bar-chord-part,.bar-cell.highlighted .bar-ann'
    if doc.count(legacy_highlight_group) != 1:
        raise ValueError('legacy highlight group anchor changed')
    doc = doc.replace(legacy_highlight_group, neutral_highlight_group, 1)
    obsolete_bar_token = '    --bar-number-strong: #75849a;\n'
    if doc.count(obsolete_bar_token) != 1:
        raise ValueError('bar-number token anchor changed')
    doc = doc.replace(obsolete_bar_token, '', 1)

    role_css = '''<style id="luminous-role-views">
/* Band/Vocal changes presentation only; no view state is persisted. */
body.edit-mode .bar-number-toggle { display: none !important; }
body:not(.edit-mode).show-bar-numbers .bar-num { display: block !important; }
body:not(.edit-mode).view-vocal .section-pair {
  display: block;
  width: min(100%, var(--four-bar-w));
  margin: 0 auto var(--space-4);
}
body:not(.edit-mode).view-vocal .section-pair > .section { margin: 0; }
body:not(.edit-mode).view-vocal .section-head { width: 100%; }
body:not(.edit-mode).view-vocal .note-type-sec,
body:not(.edit-mode).view-vocal .note-type-sec .sec-note-wrap,
body:not(.edit-mode).view-vocal .note-type-sec .sec-note-cols,
body:not(.edit-mode).view-vocal .note-type-sec .sec-note-col,
body:not(.edit-mode).view-vocal .note-type-sec .rte-editor {
  box-sizing: border-box;
  width: 100%;
  max-width: none;
  margin-left: 0;
  margin-right: 0;
}
body:not(.edit-mode).view-vocal .section .bar-row { display: none; }
body:not(.edit-mode).view-vocal .section.chords-open .bar-row { display: flex; }
/* Reserve the same repeat gutter on every Vocal row. A repeat badge must
   never force the last bar onto another line (or change stored rowSizes). */
body:not(.edit-mode).view-vocal .bar-row-main {
  flex: 0 0 calc(100% - 32px);
  max-width: calc(100% - 32px);
  flex-wrap: nowrap;
}
body:not(.edit-mode).view-vocal .bar-row-main > .bar-col {
  flex-shrink: 1;
  min-width: 0;
}
body:not(.edit-mode).view-vocal .chord-peek-btn { display: block; }
body:not(.edit-mode).view-vocal .band-lyric-cue { display: none; }
body:not(.edit-mode).view-vocal .note-type-sec .sec-note-wrap {
  display: block;
  padding-top: 0;
}
body:not(.edit-mode).view-vocal .lyric-placeholder { display: none; }

@media (max-width: 760px) {
  body:not(.edit-mode):not(.toolbar-more-open) .bar-number-toggle { display: none; }
}

@media (min-width: 1440px) {
  #sheet { width: min(100%, 1240px); }
  body:not(.edit-mode).view-band .section-pair {
    grid-template-columns: minmax(600px, 3fr) minmax(400px, 2fr);
    gap: var(--space-6);
  }
  body:not(.edit-mode).view-band .section-tag { min-height: 24px; }
}
</style>'''
    doc = doc.replace('</head>', role_css+'\n</head>', 1)

    legacy_view_tokens = ('MOBILE_VIEW', 'setMobileView', 'mobile-band', 'mobile-lyric',
                          'mobile-view-switch', 'lyric-view-btn')
    leftovers = [token for token in legacy_view_tokens if token in doc]
    if leftovers:
        raise ValueError('legacy mobile view code remains: '+', '.join(leftovers))
    if re.search(r'\.highlighted[^,{]*\.bar-num', doc):
        raise ValueError('highlight must not restyle bar numbers')
    retired_import_tokens = ('AI_START_PROMPT', 'copyAiPrompt', 'bandsheet_import.py',
                             'richTextShortcut')
    retired_leftovers = [token for token in retired_import_tokens if token in doc]
    if retired_leftovers:
        raise ValueError('retired AI import code remains: '+', '.join(retired_leftovers))
    if re.search(r'maximum-scale\s*=', doc):
        raise ValueError('zoom restriction remains')
    spec = importlib.util.spec_from_file_location("guard", ROOT / "content_guard.py")
    guard = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(guard)
    if guard.content_payload(original) != guard.content_payload(doc):
        raise ValueError("STOP: embedded song data changed")
    return doc


def blank_html(doc):
    blank = doc
    blank = blank.replace('<span class="top-brand">Resistance · Muse</span>', '<span class="top-brand">Luminous v7.0.0-alpha.2</span>')
    sections = [{"id":"intro","label":"Intro","note":"","lyric":"","noteHidden":True,
                 "color":{"bar":"#ff3b30","bg":"#fff1f0","lbl":"#b00008"},
                 "bars":[{"c":"—","a":"","h":False} for _ in range(4)],"rowSizes":[4]}]
    for name, marker, data in (("SECTIONS","DATA",sections),("FOOTER","FOOTER",{"notes":[],"links":[]}),
        ("SHEET_META","SHEET META",{"templateVersion":"v6.19","uiVersion":"7.0.0-alpha.2","sheetRevision":1,"contentUpdated":"","contentSource":"blank-baseline"})):
        end=blank.index(f"// ── END {marker} ──")
        start=blank.rfind(f"var {name} = ",0,end)
        blank=blank[:start]+f"var {name} = "+json.dumps(data,ensure_ascii=False)+";\n"+blank[end:]
    for field in ('tb-filename','tb-artist','meta-key','meta-bpm','meta-time','meta-vocalist'):
        blank=re.sub(r'(id="'+re.escape(field)+r'"[^>]*value=")[^"]*(")',r'\g<1>\g<2>',blank,count=1)
    blank=re.sub(r'<title>[^<]*</title>','<title>New Song · Luminous v7.0.0-alpha.2</title>',blank,count=1)
    return blank


def rc1_artifacts():
    """Package the accepted alpha.2 behavior; change UI labels only.

    Song blocks are checked independently and never version-bumped here.
    The blank draft's own uiVersion identifies the new shell.
    """
    doc=preview_html()
    preview=doc.replace('7.0.0-alpha.2','7.0.0-rc.1')
    blank=blank_html(doc).replace('7.0.0-alpha.2','7.0.0-rc.1')
    spec=importlib.util.spec_from_file_location('release_transfer',Path(__file__).with_name('transfer_song_trial.py'))
    transfer=importlib.util.module_from_spec(spec);spec.loader.exec_module(transfer)
    transfer.assert_equal(transfer.snapshot(doc),transfer.snapshot(preview))
    expected=transfer.snapshot(blank_html(doc))
    expected['SHEET_META']['uiVersion']='7.0.0-rc.1'
    transfer.assert_equal(expected,transfer.snapshot(blank))
    return {'preview-resistance.html':preview,'template.html':blank}


def build(release_rc1=False):
    if release_rc1:
        folder=ROOT/'releases/luminous-v7.0.0-rc.1'
        artifacts=rc1_artifacts()
        if folder.exists():
            raise ValueError('release directory already exists; never overwrite a frozen release')
        folder.mkdir(parents=True)
        for name,doc in artifacts.items():
            with (folder/name).open('x',encoding='utf-8') as f:f.write(doc)
            print(folder/name)
        return
    doc=preview_html()
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(doc, encoding='utf-8')
    blank_path=OUTPUT.with_name('luminous-v7.0.0-alpha.2-blank.html')
    blank_path.write_text(blank_html(doc),encoding='utf-8')
    print(OUTPUT)
    print(blank_path)


if __name__ == "__main__":
    import argparse
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--release-rc1',action='store_true')
    build(parser.parse_args().release_rc1)
