#!/usr/bin/env python3
"""Build a hardened trial UI from the immutable alpha.1 Git reference.

Never imports or migrates a song. Embedded musical payloads must match exactly.
"""
import hashlib
import importlib.util
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
REF = "4fb98e91389ddc021dea13996d9a72a7ed11ae75"
SOURCE = "_archive/prototypes/preview-resistance-luminous-mobile-test.html"
OUTPUT = ROOT / "_archive/prototypes/preview-luminous-v7.0.0-alpha.2.html"


def build():
    original = subprocess.check_output(["git", "show", f"{REF}:{SOURCE}"], cwd=ROOT).decode()
    if hashlib.sha256(original.encode()).hexdigest() != "b5f41bda0c5cc8c87b04a0bc322559ae5b84ce27041e800a201eefb449584bc5":
        raise ValueError("pinned source hash mismatch")
    doc = original
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
    spec = importlib.util.spec_from_file_location("guard", ROOT / "content_guard.py")
    guard = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(guard)
    if guard.content_payload(original) != guard.content_payload(doc):
        raise ValueError("STOP: embedded song data changed")
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(doc, encoding="utf-8")
    blank = doc
    blank = blank.replace('<span class="top-brand">Resistance · Muse</span>', '<span class="top-brand">Luminous v7.0.0-alpha.2</span>')
    import json
    import re
    sections = [{"id":"intro","label":"Intro","note":"","lyric":"","noteHidden":True,
                 "color":{"bar":"#ff3b30","bg":"#fff1f0","lbl":"#b00008"},
                 "bars":[{"c":"—","a":"","h":False} for _ in range(4)],"rowSizes":[4]}]
    for name, marker, data in (("SECTIONS","DATA",sections),("FOOTER","FOOTER",{"notes":[],"links":[]}),
        ("SHEET_META","SHEET META",{"templateVersion":"v6.19","uiVersion":"7.0.0-alpha.2","sheetRevision":1,"contentUpdated":"","contentSource":"blank-baseline"})):
        end=blank.index(f"// ── END {marker} ──")
        start=blank.rfind(f"var {name} = ",0,end)
        blank=blank[:start]+f"var {name} = "+json.dumps(data,ensure_ascii=False)+";\n"+blank[end:]
    for field in guard.CONTENT_FIELDS:
        blank=re.sub(r'(id="'+re.escape(field)+r'"[^>]*value=")[^"]*(")',r'\g<1>\g<2>',blank,count=1)
    blank=re.sub(r'<title>[^<]*</title>','<title>New Song · Luminous v7.0.0-alpha.2</title>',blank,count=1)
    blank_path=OUTPUT.with_name('luminous-v7.0.0-alpha.2-blank.html')
    blank_path.write_text(blank,encoding='utf-8')
    print(OUTPUT)
    print(blank_path)


if __name__ == "__main__":
    build()
