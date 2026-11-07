/* Real Chromium/CDP integration. Uses only disposable synthetic repos/profiles. */
import {spawn,spawnSync} from 'node:child_process';
import fs from 'node:fs/promises';
import path from 'node:path';
import os from 'node:os';
import assert from 'node:assert/strict';
import {fileURLToPath} from 'node:url';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const temp=await fs.mkdtemp(path.join(os.tmpdir(),'bandsheet-browser-'));
const chromePath=process.env.CHROME_BIN||'/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
const python=process.env.PYTHON_BIN||'python3';
const delay=ms=>new Promise(r=>setTimeout(r,ms));
let browser,server;const clients=[];const results=[];
class CDP {
  constructor(ws){this.ws=ws;this.next=0;this.pending=new Map();this.exceptions=[];ws.addEventListener('message',e=>{const m=JSON.parse(e.data);if(m.id){const p=this.pending.get(m.id);if(p){this.pending.delete(m.id);clearTimeout(p.timer);m.error?p.reject(Error(JSON.stringify(m.error))):p.resolve(m.result);}}if(m.method==='Runtime.exceptionThrown')this.exceptions.push(m.params.exceptionDetails.text);});}
  static async connect(url){const ws=new WebSocket(url);await new Promise((r,j)=>{ws.addEventListener('open',r,{once:true});ws.addEventListener('error',j,{once:true});});const c=new CDP(ws);clients.push(c);await c.call('Runtime.enable');return c;}
  call(method,params={}){return new Promise((resolve,reject)=>{const id=++this.next;const timer=setTimeout(()=>{this.pending.delete(id);reject(Error('CDP timeout: '+method));},15000);this.pending.set(id,{resolve,reject,timer});this.ws.send(JSON.stringify({id,method,params}));});}
  async eval(expression){const r=await this.call('Runtime.evaluate',{expression,awaitPromise:true,returnByValue:true});if(r.exceptionDetails)throw Error(JSON.stringify(r.exceptionDetails));return r.result.value;}
  close(){for(const p of this.pending.values()){clearTimeout(p.timer);p.reject(Error('CDP closed'));}this.pending.clear();this.ws.close();}
}
async function waitFor(fn,label){let last;for(let i=0;i<120;i++){try{const value=await fn();if(value)return value;}catch(error){last=error;}await delay(100);}throw Error('Timed out: '+label+(last?' / '+last.message:''));}
function runPython(code,...args){const r=spawnSync(python,['-B','-c',code,...args],{cwd:root,encoding:'utf8'});if(r.status!==0)throw Error(r.stderr);return JSON.parse(r.stdout);}
try{
 const fixture=runPython("import sys,json;sys.path.insert(0,'src/intake');from git_store import initialize_lab;import song_data_contract as c;s=c.load_json('tests/fixtures/song-data/representative.json');s['settings']['chordFont']='Synthetic preserved font';del s['sections'][0]['rowSizes'];initialize_lab(sys.argv[1],s);print(json.dumps(s))",path.join(temp,'lab'));
 server=spawn(python,['-B','tools/synthetic_save_lab.py','serve','--repo',path.join(temp,'lab/writer.git')],{cwd:root,stdio:['ignore','pipe','pipe']});
 let output='',errors='';server.stdout.on('data',b=>output+=b);server.stderr.on('data',b=>errors+=b);
 const url=await waitFor(()=>{if(server.exitCode!==null)throw Error(errors);return output.includes('\n')?JSON.parse(output.split('\n')[0]).url:null;},'server');
 const profile=path.join(temp,'profile');
 browser=spawn(chromePath,['--headless=new','--remote-debugging-port=0','--user-data-dir='+profile,'--disable-background-networking','--no-first-run','--no-default-browser-check','--disable-sync','--disable-extensions','about:blank'],{stdio:'ignore'});
 const port=await waitFor(async()=>{const s=await fs.readFile(path.join(profile,'DevToolsActivePort'),'utf8');return s.split('\n')[0];},'Chromium');
 async function open(){const tab=await (await fetch(`http://127.0.0.1:${port}/json/new?${encodeURIComponent(url)}`,{method:'PUT'})).json();const c=await CDP.connect(tab.webSocketDebuggerUrl);await waitFor(()=>c.eval('typeof bandsheetRevisionState === "function"'),'revision client');return c;}
 let page=await open();
 const initial=await page.eval('bandsheetRevisionState()');
 assert.deepEqual(initial.base,fixture);
 assert.deepEqual(initial.payload,{metadata:fixture.metadata,sections:fixture.sections,footer:fixture.footer,settings:fixture.settings,extensions:fixture.extensions});
 assert.equal(await page.eval('hasUnsavedChanges()'),false);
 await page.eval('toggleEditMode();toggleEditMode();window.dispatchEvent(new Event("resize"));');
 await delay(200);
 assert.equal(await page.eval('hasUnsavedChanges()'),false);
 const first=await page.eval('saveToFile()');assert.equal(first.changed,false);assert.equal(first.persistence,'verified-test-remote');
 results.push('no-change startup/render/edit-mode/resize/save; custom settings and absent rowSizes preserved');
 await page.eval('toggleEditMode();document.getElementById("tb-filename").focus();document.getElementById("tb-filename").select();');
 await page.call('Input.insertText',{text:'Synthetic browser title'});
 await page.eval('(()=>{const e=document.querySelector(".bar-chord");e.focus();const r=document.createRange();r.selectNodeContents(e);const s=getSelection();s.removeAllRanges();s.addRange(r)})()');
 await page.call('Input.insertText',{text:'Dm'});
 await page.eval('(()=>{const e=document.querySelector(".rte-editor");e.focus();const r=document.createRange();r.selectNodeContents(e);const s=getSelection();s.removeAllRanges();s.addRange(r)})()');
 await page.call('Input.insertText',{text:'Synthetic lyric ไทย'});
 const expected=structuredClone(fixture);expected.metadata.title='Synthetic browser title';expected.sections[0].bars[0].c='Dm';expected.sections[1].cols[0]='Synthetic lyric ไทย';
 const edited=await page.eval('saveToFile()');
 assert.equal(edited.revision.contentRevision,2);assert.equal(edited.revision.provenance.parentRevisionHash,first.revisionHash);
 for(const k of ['metadata','sections','footer','settings','extensions'])assert.deepEqual(edited.revision[k],expected[k]);
 assert.equal(await page.eval('hasUnsavedChanges()'),false);
 const repeat=await page.eval('saveToFile()');assert.equal(repeat.changed,false);assert.equal(repeat.revisionHash,edited.revisionHash);
 results.push('real DOM metadata/chord/lyric input; full-field equality; duplicate Save without revision increment');
 const reopened=await open();assert.deepEqual((await reopened.eval('bandsheetRevisionState()')).base,edited.revision);
 assert.equal(await reopened.eval('document.querySelector(".rte-editor").textContent'),'Synthetic lyric ไทย');
 assert.equal(await reopened.eval('document.querySelector(".bar-chord").textContent'),'Dm');
 results.push('new browser tab reopens remote revision and renders exact chord/lyric');
 await reopened.eval('document.getElementById("tb-filename").value="Synthetic offline edit";document.getElementById("tb-filename").dispatchEvent(new Event("input",{bubbles:true}));');
 await fs.rename(path.join(temp,'lab/remote.git'),path.join(temp,'lab/offline.git'));
 const failed=await reopened.eval('saveToFile()');assert.ok(failed.error);assert.equal(await reopened.eval('bandsheetRevisionState().state'),'pending-or-conflict');assert.equal(await reopened.eval('hasUnsavedChanges()'),true);
 const pending=await reopened.eval('bandsheetRevisionState().pending');
 await fs.rename(path.join(temp,'lab/offline.git'),path.join(temp,'lab/remote.git'));
 const retried=await reopened.eval('saveToFile()');assert.equal(retried.saveId,pending.saveId);assert.equal(retried.revision.metadata.title,'Synthetic offline edit');
 results.push('remote unavailable never acknowledged; retry retains save ID and saves exact pending edit');
 // This tab is now stale; its Save must not overwrite the newer remote revision.
 await page.eval('document.getElementById("tb-filename").value="Conflicting synthetic edit";document.getElementById("tb-filename").dispatchEvent(new Event("input",{bubbles:true}));');
 const conflict=await page.eval('saveToFile()');assert.ok(conflict.error.includes('stale parent'));assert.equal(await page.eval('hasUnsavedChanges()'),true);
 results.push('two-tab stale-parent conflict preserves unsaved local edit');
 // Recovery is a cache, not an acknowledgement. Clear competing tab cache for this isolated test.
 await reopened.eval('localStorage.clear();document.getElementById("tb-filename").value="Crash recovery draft";document.getElementById("tb-filename").dispatchEvent(new Event("input",{bubbles:true}));');
 await delay(1000);reopened.call('Page.crash').catch(()=>{});await delay(500);
 const recovered=await open();assert.equal(await recovered.eval('document.getElementById("tb-filename").value'),'Crash recovery draft');assert.equal(await recovered.eval('bandsheetRevisionState().state'),'recovered-local');assert.equal(await recovered.eval('hasUnsavedChanges()'),true);
 results.push('renderer crash recovers local draft but does not claim Git persistence');
 const tamper=await recovered.eval('(async()=>{const s=bandsheetRevisionState();const r=await fetch("/api/save",{method:"POST",headers:{"Content-Type":"application/json","X-Bandsheet-Token":BANDSHEET_WRITER.token},body:JSON.stringify({saveId:"browser-tamper-0001",songId:s.base.songId,expectedParentHash:"0".repeat(64),payload:s.payload})});return r.status})()');assert.equal(tamper,409);
 const unauthorized=await recovered.eval('(async()=>{const r=await fetch("/api/save",{method:"POST",headers:{"Content-Type":"application/json"},body:"{}"});return r.status})()');assert.equal(unauthorized,403);
 results.push('tampered parent and missing writer token rejected');
 assert.deepEqual(page.exceptions,[]);assert.deepEqual(recovered.exceptions,[]);
 const verification=runPython("import sys,json;sys.path.insert(0,'src/intake');from git_store import Writer;print(json.dumps(Writer(sys.argv[1]).verify()))",path.join(temp,'lab/writer.git'));
 console.log(JSON.stringify({status:'PASS',browser:await recovered.eval('navigator.userAgent'),cases:results,verification,limitations:['local bare test remote only; no GitHub push','Chromium desktop only; Safari/mobile/offline file URLs not certified','renderer crash tested; storage eviction/power-loss not certified']},null,2));
}finally{
 for(const c of clients)c.close();
 if(browser)browser.kill('SIGTERM');if(server)server.kill('SIGTERM');
 await delay(500);await fs.rm(temp,{recursive:true,force:true});
}
