#!/usr/bin/env python3
"""Create NEW scratch P0 test fixtures; never regenerate tracked prototypes."""
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile

ROOT=Path(__file__).resolve().parents[1]
def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

def create():
    b=load('p0_build',ROOT/'tools/build_luminous.py')
    t=load('p0_transfer',ROOT/'tools/transfer_song_trial.py')
    source=(ROOT/'songs/starlight.html').read_text()
    clean=t.render(source,b.blank_html(b.preview_html()))
    expected=t.snapshot(source)
    proof=r'''
<script id="p0-proof">
var P0_EXPECTED=__EXPECTED_JSON__;
function p0Stable(x){if(Array.isArray(x))return x.map(p0Stable);if(x&&typeof x==='object'){var o={};Object.keys(x).sort().forEach(k=>o[k]=p0Stable(x[k]));return o;}return x;}
var P0_COUNTS=0,P0_NODES=Array.from(document.querySelectorAll('#sheet .section,#sheet .bar-cell,#sheet .rte-editor'));
var P0_RENDER_NAME=typeof window.renderData==='function'?'renderData':'render';
var P0_ORIGINAL_RENDER=window[P0_RENDER_NAME];
window[P0_RENDER_NAME]=function(){P0_COUNTS++;return P0_ORIGINAL_RENDER.apply(this,arguments)};
var P0_CHILD_MUTATIONS=0;
new MutationObserver(records=>P0_CHILD_MUTATIONS+=records.length).observe(document.getElementById('sheet'),{childList:true,subtree:true});
function p0Capture(){
var metadata={};Object.keys(P0_EXPECTED.metadata).forEach(k=>metadata[k]=document.getElementById(k).value);
var now={metadata:metadata,SECTIONS:SECTIONS,FOOTER:FOOTER,SETTINGS:SETTINGS,SHEET_META:SHEET_META};
var nodes=Array.from(document.querySelectorAll('#sheet .section,#sheet .bar-cell,#sheet .rte-editor'));
var fields={};Object.keys(now).forEach(k=>fields[k]=JSON.stringify(p0Stable(now[k]))===JSON.stringify(p0Stable(P0_EXPECTED[k])));
function width(sel){return Math.round((document.querySelector(sel)?.getBoundingClientRect().width||0)*100)/100}
var geometry={sheet:width('#sheet'),pair:width('.section-pair'),chord:width('.section-pair > .section'),lyric:width('.section-pair > .note-type-sec'),cell:width('.bar-cell')};
document.getElementById('p0-result').textContent=JSON.stringify({fields:fields,allEqual:Object.values(fields).every(Boolean),renders:P0_COUNTS,childMutations:P0_CHILD_MUTATIONS,nodeIdentity:nodes.length===P0_NODES.length&&nodes.every((n,i)=>n===P0_NODES[i]),sections:document.querySelectorAll('#sheet .section').length,bars:document.querySelectorAll('#sheet .bar-cell').length,lyrics:document.querySelectorAll('#sheet .rte-editor').length,anchor:document.querySelector('.focus-anchor-target')?.dataset.bi||null,scrollY:window.scrollY,scale:window.visualViewport?.scale||1,width:window.innerWidth,geometry:geometry});
}
var panel=document.createElement('div');panel.style='position:fixed;right:4px;top:100px;z-index:9999;background:white;max-width:380px;padding:8px;border:1px solid #888';
panel.innerHTML='<button id="p0-capture">Capture P0</button> <button id="p0-scroll">Scroll P0</button><pre id="p0-result" style="white-space:pre-wrap;font-size:11px"></pre>';
document.body.appendChild(panel);
document.getElementById('p0-capture').onclick=p0Capture;
document.getElementById('p0-scroll').onclick=function(){window.scrollTo(0,700);requestAnimationFrame(()=>requestAnimationFrame(p0Capture))};
p0Capture();window.addEventListener('resize',()=>requestAnimationFrame(()=>requestAnimationFrame(p0Capture)));
</script>
'''.replace('__EXPECTED_JSON__',json.dumps(expected,ensure_ascii=False).replace('<','\u003c'),1)
    parent=ROOT/'_work/audit';parent.mkdir(exist_ok=True,parents=True)
    folder=Path(tempfile.mkdtemp(prefix='p0-zoom-',dir=parent))
    (folder/'candidate.html').write_text(clean)
    (folder/'runtime.html').write_text(clean.replace('</body>',proof+'</body>'))
    baseline=t.render(source,(ROOT/'_archive/prototypes/luminous-v7.0.0-alpha.2-blank.html').read_text())
    (folder/'baseline-runtime.html').write_text(baseline.replace('</body>',proof+'</body>'))
    (folder/'evidence.json').write_text(json.dumps({'source':'songs/starlight.html','sourceSha256':hashlib.sha256(source.encode()).hexdigest(),'candidateSha256':hashlib.sha256(clean.encode()).hexdigest(),'embeddedEquality':True,'runtime':'pending','safari':'not tested'},indent=2))
    print(folder)

if __name__=='__main__':create()
