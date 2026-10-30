import importlib.util
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
    def __init__(self):super().__init__();self.active=False;self.scripts=[]
    def handle_starttag(self,tag,attrs):
        if tag=='script':self.active=True;self.scripts.append('')
    def handle_endtag(self,tag):
        if tag=='script':self.active=False
    def handle_data(self,data):
        if self.active:self.scripts[-1]+=data

class LayoutP0Tests(unittest.TestCase):
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
