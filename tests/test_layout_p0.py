import importlib.util
from collections import Counter
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import shutil
import subprocess
import unittest

ROOT=Path(__file__).resolve().parents[1]
def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
b=load('p0_builder',ROOT/'tools/build_luminous.py')
t=load('p0_snapshot',ROOT/'tools/transfer_song_trial.py')

class Scripts(HTMLParser):
    def __init__(self):super().__init__();self.active=False;self.scripts=[];self.ids=[]
    def handle_starttag(self,tag,attrs):
        self.ids.extend(value for key,value in attrs if key=='id' and value)
        if tag=='script':self.active=True;self.scripts.append('')
    def handle_endtag(self,tag):
        if tag=='script':self.active=False
    def handle_data(self,data):
        if self.active:self.scripts[-1]+=data

class LayoutP0Tests(unittest.TestCase):
    def test_export_removes_runtime_sheet_and_focus_controls(self):
        node=shutil.which('node')
        if not node:self.skipTest('Node unavailable')
        doc=b.preview_html();start=doc.index('function cleanRuntimeHtml(html){')
        end=doc.index('\nfunction filenameSlug',start)
        harness=r'''
const vm=require('vm'),assert=require('assert');const c={};
vm.createContext(c);vm.runInContext(FUNCTION,c);
const input='<html style="--cell-w:130px"><body class="has-focus-anchor"><div id="sheet" style="--note-content-w:517px"><div data-focus-bound="1"><div>runtime chart</div></div></div>\n<div class="color-popup" id="colorPopup"></div><button id="focus-return" class="focus-return">old</button></body></html>';
const out=c.cleanRuntimeHtml(input);
assert.ok(out.includes('<div id="sheet"></div>'));
assert.ok(!out.includes('data-focus-bound'));
assert.ok(!out.includes('id="focus-return"'));
assert.ok(out.includes('id="colorPopup"'));
assert.equal(c.cleanRuntimeHtml(out),out);
'''
        result=subprocess.run([node,'-e','const FUNCTION='+json.dumps(doc[start:end])+';\n'+harness],text=True,capture_output=True)
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)

    def test_exported_focus_button_is_rebound_without_duplicates(self):
        node=shutil.which('node')
        if not node:self.skipTest('Node unavailable')
        doc=b.preview_html()
        start=doc.index('  function ensureFocusReturn() {')
        end=doc.index('\n  function renderFocusAnchor()',start)
        function=doc[start:end]
        harness=r'''
const vm=require('vm'),assert=require('assert');
for(const exported of [false,true]){
 let button=exported?{id:'focus-return',textContent:'old label'}:null;
 let appends=0,returns=0;
 const c={window:{returnToFocus(){returns++}},document:{
  getElementById(){return button},createElement(){return {}},
  body:{appendChild(b){button=b;appends++}}
 }};
 vm.createContext(c);vm.runInContext(FUNCTION,c);
 for(let i=0;i<3;i++)c.ensureFocusReturn();
 assert.equal(appends,exported?0:1);
 assert.equal(typeof button.onclick,'function');button.onclick();
 assert.equal(returns,1);
}
'''
        result=subprocess.run([node,'-e','const FUNCTION='+json.dumps(function)+';\n'+harness],text=True,capture_output=True)
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)

    @classmethod
    def setUpClass(cls):
        cls.original=subprocess.check_output(['git','show',f'{b.REF}:{b.SOURCE}'],cwd=ROOT,text=True)
        cls.candidate=b.preview_html()

    def test_viewport_and_geometry_only(self):
        self.assertNotIn('maximum-scale=',self.candidate)
        self.assertIn('content="width=device-width, initial-scale=1"',self.candidate)
        self.assertNotIn('LAST_VISUAL_CAP',self.candidate)
        self.assertIn('function renderData(){',self.candidate)
        self.assertIn('function updateLayout()',self.candidate)
        css=self.candidate.split('<style id="luminous-layout-p0">',1)[1].split('</style>',1)[0]
        self.assertNotRegex(css,r'transform\s*:\s*scale\(')
        self.assertNotIn('#sheet',css)
        self.assertNotIn('grid-template-columns',css)
        self.assertIn('#sheet{width:min(100%,1120px);margin:0 auto}',self.candidate)
        self.assertIn('grid-template-columns: minmax(520px, 3fr) minmax(360px, 2fr);',self.candidate)
        self.assertIn('var w=Math.max(minW,Math.min(maxW,Math.floor(avail/cols)));',self.candidate)

    def test_all_payloads_and_revision_unchanged(self):
        t.assert_equal(t.snapshot(self.original),t.snapshot(self.candidate))
        blank=b.blank_html(self.candidate)
        self.assertEqual(t.snapshot(blank)['SECTIONS'][0]['bars'][0]['c'],'—')
        existing=(ROOT/'_archive/prototypes/luminous-v7.0.0-alpha.2-blank.html').read_text()
        t.assert_equal(t.snapshot(existing),t.snapshot(blank))

    def test_generated_javascript_syntax(self):
        node=shutil.which('node')
        if not node:self.skipTest('Node unavailable')
        parser=Scripts();parser.feed(self.candidate)
        for script in parser.scripts:
            p=subprocess.run([node,'--check'],input=script,text=True,capture_output=True)
            self.assertEqual(p.returncode,0,p.stderr)

    def test_static_html_ids_are_unique(self):
        parser=Scripts();parser.feed(self.candidate)
        duplicates=sorted(value for value,count in Counter(parser.ids).items() if count>1)
        self.assertEqual(duplicates,[])

    def test_role_view_is_responsive_session_state_only(self):
        self.assertIn('aria-label="Performance view"',self.candidate)
        self.assertIn("onclick=\"setPerformanceView('band')\"",self.candidate)
        self.assertIn("onclick=\"setPerformanceView('vocal')\"",self.candidate)
        self.assertIn("window.matchMedia('(max-width: 760px)').matches ? 'vocal' : 'band'",self.candidate)
        self.assertIn("document.body.dataset.performanceView = PERFORMANCE_VIEW",self.candidate)
        for legacy in ('MOBILE_VIEW','setMobileView','mobile-band','mobile-lyric',
                       'mobile-view-switch','lyric-view-btn'):
            self.assertNotIn(legacy,self.candidate)
        state=self.candidate[self.candidate.index('var PERFORMANCE_VIEW'):self.candidate.index('window.toggleToolbarMore')]
        self.assertNotIn('localStorage',state)
        self.assertNotIn('sessionStorage',state)
        self.assertNotIn('document.cookie',state)
        self.assertIn('#sheet { width: min(100%, 1240px); }',self.candidate)
        self.assertIn('width: min(100%, var(--four-bar-w));',self.candidate)
        self.assertIn('body:not(.edit-mode).view-vocal .note-type-sec .sec-note-cols,',self.candidate)

    def test_section_color_has_one_rendered_source(self):
        mapped="var renderedTone=getComputedStyle(el);inp.style.background=renderedTone.backgroundColor;inp.style.color=renderedTone.color;inp.style.borderColor=renderedTone.borderLeftColor;"
        raw="inp.style.background=(SECTIONS[idx].color||{}).bg"
        self.assertEqual(self.candidate.count(mapped),1)
        self.assertNotIn(raw,self.candidate)
        self.assertIn('var tone = headingColor(section.color || PRESETS[si % PRESETS.length]);',self.candidate)

    def test_bar_number_weight_is_uniform(self):
        self.assertNotIn('--bar-number-strong',self.candidate)
        self.assertNotIn('.bar-col:first-child .bar-num',self.candidate)
        self.assertNotRegex(self.candidate,r'\.highlighted[^,{]*\.bar-num')
        self.assertIn('body:not(.edit-mode) .bar-num { display: none !important; }',self.candidate)

    def test_bar_number_display_toggle_is_ephemeral(self):
        self.assertIn('id="bar-number-btn"',self.candidate)
        self.assertIn('onclick="toggleBarNumbers()"',self.candidate)
        self.assertIn("var BAR_NUMBERS_VISIBLE = false",self.candidate)
        self.assertIn("classList.toggle('show-bar-numbers', BAR_NUMBERS_VISIBLE)",self.candidate)
        self.assertIn("body:not(.edit-mode).show-bar-numbers .bar-num { display: block !important; }",self.candidate)
        self.assertIn('body.edit-mode .bar-number-toggle { display: none !important; }',self.candidate)
        state=self.candidate[self.candidate.index('var BAR_NUMBERS_VISIBLE'):self.candidate.index('var PERFORMANCE_VIEW')]
        self.assertNotIn('localStorage',state)
        self.assertNotIn('sessionStorage',state)
        self.assertNotIn('SETTINGS',state)

    def test_retired_ai_import_prompt_is_absent(self):
        for token in ('AI_START_PROMPT','copyAiPrompt','bandsheet_import.py'):
            self.assertNotIn(token,self.candidate)
        self.assertIn('function injectData(html){',self.candidate)

    def test_lyric_formatting_uses_native_contenteditable_shortcuts(self):
        self.assertNotIn('richTextShortcut',self.candidate)
        self.assertNotIn("document.execCommand(cmd,false,null)",self.candidate)
        self.assertIn('ed.contentEditable=EDIT_MODE',self.candidate)
        self.assertIn('ed.oninput=ed.onblur=',self.candidate)

    def test_real_resize_scroll_handlers_do_not_render_or_mutate(self):
        node=shutil.which('node')
        if not node:self.skipTest('Node unavailable')
        parser=Scripts();parser.feed(self.candidate)
        auto_hide=parser.scripts[0]
        core=self.candidate[self.candidate.index('function updateCellWidthCore(){'):self.candidate.index('function measureRowContentWidth(row){')]
        layout=(ROOT/'tools/luminous_layout.js').read_text()
        # Run the real handlers with mutation traps and a render tripwire.
        harness=r'''
const vm=require('vm'),assert=require('assert');
const handlers={},vvHandlers={},frames=[],styles={},classes={};let layouts=0;
const trap=new Proxy({}, {get(){return trap},set(){throw Error('payload mutation')},deleteProperty(){throw Error('payload deletion')}});
const sheet={clientWidth:1600};
const doc={documentElement:{clientWidth:1600,scrollHeight:10000,style:{setProperty(k,v){styles[k]=v}}},body:{classList:{toggle(k,v){classes[k]=v}}},
 getElementById(id){return id==='sheet'?sheet:{offsetHeight:56}},
 addEventListener(k,f){(handlers['doc:'+k]??=[]).push(f)},dispatchEvent(e){if(e.type==='bandsheet:layout')layouts++}};
const win={innerWidth:1600,innerHeight:800,scrollY:500,visualViewport:{scale:1,addEventListener(k,f){(vvHandlers[k]??=[]).push(f)}},
 addEventListener(k,f){(handlers[k]??=[]).push(f)}};
const c={window:win,document:doc,SECTIONS:trap,SETTINGS:trap,FOOTER:trap,SHEET_META:trap,
 VIEW:'mini',EDIT_MODE:false,Event:class{constructor(type){this.type=type}},
 requestAnimationFrame(f){frames.push(f);return frames.length},
 getComputedStyle(){return {paddingLeft:'24',paddingRight:'24',getPropertyValue(){return '3'}}},
 visualColsFor(){return win.innerWidth<=900?4:8},syncNoteWidths(){},
 render(){throw Error('data render called')},renderData(){throw Error('data render called')}};
vm.createContext(c);vm.runInContext(CORE+'\n'+LAYOUT+'\n'+AUTO,c);
function fire(k){for(const f of handlers[k]||[])f()};function flush(){while(frames.length)frames.shift()()};
fire('doc:DOMContentLoaded');
for(let i=0;i<10;i++)fire('resize');flush();assert.equal(layouts,1);
win.innerWidth=600;fire('resize');flush();assert.equal(layouts,2);
win.visualViewport.scale=2;for(const f of vvHandlers.resize)f();flush();assert.equal(layouts,2);
win.scrollY=900;fire('scroll');flush();assert.equal(layouts,2);assert.equal(classes['bars-hidden'],true);
win.scrollY=700;fire('scroll');flush();assert.equal(layouts,2);assert.equal(classes['bars-hidden'],false);
win.visualViewport.scale=1;for(const f of vvHandlers.resize)f();flush();assert.equal(layouts,3);
assert.equal(win.scrollY,700);assert.ok(parseInt(styles['--cell-w'])>0);
// Negative control: the former resize handler must hit the render tripwire.
c.LAST_VISUAL_CAP=4;c.currentVisualCap=()=>8;
assert.throws(()=>vm.runInContext("var cap=currentVisualCap(); if(!EDIT_MODE&&cap!==LAST_VISUAL_CAP){LAST_VISUAL_CAP=cap;render();}",c),/data render called/);
console.log('PASS resize coalescing, pinch defer, scroll-only hide, payload traps, negative control');
'''
        code='const CORE='+json.dumps(core)+',LAYOUT='+json.dumps(layout)+',AUTO='+json.dumps(auto_hide)+';\n'+harness
        p=subprocess.run([node,'-e',code],text=True,capture_output=True)
        self.assertEqual(p.returncode,0,p.stdout+p.stderr)

if __name__=='__main__':unittest.main()
