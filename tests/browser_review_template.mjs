// Runs on a disposable Chromium profile. Optional first argument: the pinned Hysteria review JSON.
import assert from 'node:assert/strict';
import { spawn, spawnSync } from 'node:child_process';
import fs from 'node:fs/promises';
import { once } from 'node:events';
import os from 'node:os';
import path from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

const checkout = path.dirname(path.dirname(fileURLToPath(import.meta.url)));
const templateFolder = path.join(checkout, 'src/sheet/templates/luminous-v7.0.0-rc.4-review');
const template = path.join(templateFolder, 'template.html');
const fixturePath = path.join(checkout, 'tests/fixtures/song-data/representative.json');
const hysteriaPath = process.argv[2] ? path.resolve(process.argv[2]) : null;
const root = await fs.mkdtemp(path.join(os.tmpdir(), 'bandsheet-review-template-'));
const temp = path.join(root, 'browser-profile');
const fixture = JSON.parse(await fs.readFile(fixturePath, 'utf8'));
const hysteriaRevision = hysteriaPath ? JSON.parse(await fs.readFile(hysteriaPath, 'utf8')) : null;
if (hysteriaRevision) {
  assert.equal(hysteriaRevision.songId, 'review-hysteria');
  assert.ok(hysteriaRevision.provenance.sourceRef.endsWith(
    '#sha256=3418e810eafe653418e5e00e92e8d23014d950b55bdf0960abb7174a0cdd1212'));
}

function build(...args) {
  const processResult = spawnSync(process.env.PYTHON_BIN || 'python3',
    ['-B', path.join(templateFolder, 'build.py'), ...args], {encoding: 'utf8'});
  assert.equal(processResult.status, 0, processResult.stderr || processResult.error?.message);
}
build('--check');
build('--song-json', fixturePath, '--output', path.join(root, 'synthetic-review.html'));
if (hysteriaPath) build('--song-json', hysteriaPath, '--output', path.join(root, 'hysteria-review.html'));

const chrome = process.env.CHROME_BIN ?? '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
const browser = spawn(chrome, [
  '--headless=new', '--remote-debugging-port=0', '--no-first-run', '--disable-background-networking',
  '--no-default-browser-check', '--disable-sync', '--disable-extensions',
  '--proxy-server=http://127.0.0.1:9', '--user-data-dir=' + temp, 'about:blank'
], { stdio: 'ignore' });
const clients = [];
let passed = false;
const cases = [];
const delay = ms => new Promise(resolve => setTimeout(resolve, ms));
async function waitFor(get, label) {
  for (let i = 0; i < 100; i++) {
    try { const value = await get(); if (value) return value; } catch {}
    await delay(100);
  }
  throw Error('Timed out: ' + label);
}
class Session {
  constructor(ws) {
    this.ws = ws;
    this.pending = new Map();
    this.errors = [];
    this.id = 0;
    ws.addEventListener('message', event => {
      const message = JSON.parse(event.data);
      if (message.method === 'Runtime.exceptionThrown') this.errors.push(message.params.exceptionDetails);
      const cb = this.pending.get(message.id);
      if (cb) {
        this.pending.delete(message.id);
        clearTimeout(cb.timer);
        if (message.error) cb.reject(Error(message.error.message));
        else cb.resolve(message.result);
      }
    });
  }
  call(method, params = {}) {
    return new Promise((resolve, reject) => {
      const id = ++this.id;
      const timer = setTimeout(() => { this.pending.delete(id); reject(Error('CDP timeout ' + method)); }, 12000);
      this.pending.set(id, {resolve, reject, timer});
      this.ws.send(JSON.stringify({id, method, params}));
    });
  }
  async eval(expression) {
    const r = await this.call('Runtime.evaluate', {expression, returnByValue: true, awaitPromise: true});
    if (r.exceptionDetails) throw Error(r.exceptionDetails.exception?.description ?? r.exceptionDetails.text);
    return r.result.value;
  }
}
const readPage = `(() => {
  const ids = {title:'tb-filename',artist:'tb-artist',key:'meta-key',bpm:'meta-bpm',timeSignature:'meta-time',vocalist:'meta-vocalist'};
  const sections = Array.from(document.querySelectorAll('#sheet .section[data-si]'), sec => {
    const bars = Array.from(sec.querySelectorAll('.bar-cell[data-bi]'), cell => ({
      i: Number(cell.dataset.bi), n: cell.querySelector('.bar-num')?.textContent,
      chords: Array.from(cell.querySelectorAll('.bar-chord, .bar-chord-part'), el => el.textContent),
      annotation: cell.querySelector('.bar-ann')?.value,
      highlighted: cell.classList.contains('highlighted')
    }));
    return {
      i:Number(sec.dataset.si), label:sec.querySelector('.section-tag')?.textContent,
      lyrics:Array.from(sec.querySelectorAll('.rte-editor'), el => el.innerHTML),
      bars
    };
  });
  return {
    metadata:Object.fromEntries(Object.entries(ids).map(([key,id])=>[key,document.getElementById(id).value])),
    sections:SECTIONS, footer:FOOTER, settings:SETTINGS, sheetMeta:SHEET_META, dom:sections
  };
})()`;
try {
  const port = await waitFor(async () => (await fs.readFile(path.join(temp,'DevToolsActivePort'),'utf8')).split('\n')[0], 'Chromium');
  async function open(name, width, height) {
    const response = await fetch('http://127.0.0.1:' + port + '/json/new?about:blank', { method: 'PUT' });
    assert.equal(response.ok, true);
    const ws = new WebSocket((await response.json()).webSocketDebuggerUrl);
    await new Promise((resolve,reject)=>{ws.addEventListener('open',resolve,{once:true});ws.addEventListener('error',reject,{once:true});});
    const s = new Session(ws);
    clients.push(s);
    await s.call('Runtime.enable');
    await s.call('Network.enable');
    await s.call('Network.setBlockedURLs', {urls:['http://*','https://*']});
    await s.call('Emulation.setDeviceMetricsOverride', {width,height,deviceScaleFactor:1,mobile:width<600});
    const nav = await s.call('Page.navigate', {url:pathToFileURL(path.resolve(root,name)).href});
    assert.equal(nav.errorText, undefined);
    await waitFor(() => s.eval("document.readyState === 'complete' && location.protocol === 'file:'"), name);
    const count = await s.eval("document.querySelectorAll('#sheet .section[data-si]').length");
    if (!count) {
      const debug = await s.eval("({url:location.href, title:document.title, ready:document.readyState, render:typeof render, sections:typeof SECTIONS, revision:typeof bandsheetRevisionState, sheet:document.getElementById('sheet')?.children.length, scripts:document.scripts.length, details:Array.from(document.getElementById('sheet')?.children||[],el=>el.className).slice(0,5), directRender:(()=>{try{render();return document.getElementById('sheet')?.children.length}catch(e){return String(e)}})()})");
      throw Error(name + ' rendered zero sections: ' + JSON.stringify({debug, errors:s.errors.map(e=>({text:e.text, line:e.lineNumber, column:e.columnNumber, error:e.exception?.description}))}));
    }
    return s;
  }
  const downloaded = await fs.mkdtemp(path.join(root,'downloads-'));
  const fileSizes = {};
  async function download(page, filename) {
    const folder = await fs.mkdtemp(path.join(downloaded,'case-'));
    await page.call('Browser.setDownloadBehavior', {behavior:'allow',downloadPath:folder});
    await click(page, '#local-save-html-btn');
    const full = path.join(folder,filename);
    await waitFor(async () => (await fs.stat(full)).size > 0, filename+' · '+await page.eval("document.getElementById('save-state').textContent"));
    assert.match(await page.eval("document.getElementById('save-state').textContent"),/HTML download requested/);
    const bytes = await fs.readFile(full);
    const html = bytes.toString('utf8');
    for (const id of ['sheet','rhythmPicker','bpNotes','swatches','swatches-light','toast']) {
      assert.match(html,new RegExp('<div[^>]* id="' + id + '"[^>]*></div>'),id+' is serialized empty');
    }
    return {path:full, bytes};

  }
  async function click(page, selector) {
    const rect = await page.eval(`(() => {
      const el = document.querySelector(${JSON.stringify(selector)});
      el.scrollIntoView({block:'center',inline:'center'});
      const r=el.getBoundingClientRect();
      return {x:r.x+r.width/2,y:r.y+r.height/2,width:r.width};
    })()`);
    assert.ok(rect.width,selector+' is visible');
    await page.call('Input.dispatchMouseEvent',{type:'mousePressed',button:'left',clickCount:1,x:rect.x,y:rect.y});
    await page.call('Input.dispatchMouseEvent',{type:'mouseReleased',button:'left',clickCount:1,x:rect.x,y:rect.y});
  }
  async function readRevision(page) {
    const stored = await page.eval("JSON.parse(document.getElementById('bandsheet-revision').textContent)");
    const live = await page.eval(readPage);
    for (const key of ['metadata','sections','footer','settings']) assert.deepEqual(live[key],stored[key]);
    assert.equal(live.sheetMeta.contentHash,await page.eval("RevisionProtocol.hash(RevisionProtocol.semantic(JSON.parse(document.getElementById('bandsheet-revision').textContent)))"));
    assert.equal(live.sheetMeta.revisionHash,await page.eval("RevisionProtocol.hash(JSON.parse(document.getElementById('bandsheet-revision').textContent))"));
    assert.equal(await page.eval('hasUnsavedChanges()'),false);
    assert.equal(await page.eval('document.body.dataset.performanceView'),'both');
    return {stored,live};
  }

  async function selectWord(page, length) {
    await page.eval(`(() => {
      const editor = document.querySelector('.rte-editor');
      editor.focus();
      const text = document.createTreeWalker(editor,NodeFilter.SHOW_TEXT).nextNode();
      const range = document.createRange();
      range.setStart(text,0);
      range.setEnd(text,${length});
      window.getSelection().removeAllRanges();
      window.getSelection().addRange(range);
    })()`);
  }
  async function applyFormatting(page) {
    assert.equal(await page.eval("document.querySelector('[aria-label=\"Lyric font\"]')"), null);
    for (const kind of ['bold','italic','underline']) await click(page,'.lyric-' + kind);
  }
  async function readFormatting(page, text) {
    return page.eval(`(() => {
      const editor = document.querySelector('.rte-editor');
      const walk = document.createTreeWalker(editor,NodeFilter.SHOW_TEXT);
      let node;
      while ((node=walk.nextNode())) if (node.textContent===${JSON.stringify(text)}) {
        const style=getComputedStyle(node.parentElement);
        let underlined=false;
        for (let el=node.parentElement; el && el!==editor; el=el.parentElement) {
          underlined ||= getComputedStyle(el).textDecorationLine.includes('underline');
        }
        return {weight:Number(style.fontWeight),italic:style.fontStyle,underlined};
      }
      return null;
    })()`);
  }
  function assertFormat(result) {
    assert.ok(result && result.weight>=700,JSON.stringify(result));
    assert.equal(result.italic,'italic');
    assert.equal(result.underlined,true);
  }
  function assertOnlyFormattedLyric(actual, base) {
    const comparable = structuredClone(actual);
    const index = comparable.sections.findIndex(section => section.type==='note');
    assert.notEqual(comparable.sections[index].cols[0],base.sections[index].cols[0]);
    comparable.sections[index].cols[0]=base.sections[index].cols[0];
    comparable.contentRevision=base.contentRevision;
    comparable.provenance=base.provenance;
    assert.deepEqual(comparable,base);
  }
  async function assertBothViews(page) {
    assert.equal(await page.eval("document.documentElement.scrollWidth"),await page.eval("document.documentElement.clientWidth"));
    for (const mode of ['band','vocal','both']) {
      await click(page,'#'+mode+'-view-btn');
      assert.equal(await page.eval('document.body.dataset.performanceView'),mode);
      assert.equal(await page.eval('hasUnsavedChanges()'),false);
    }
    const visible = await page.eval(`[
      Array.from(document.querySelectorAll('.bar-cell[data-bi]')).filter(el=>el.getClientRects().length).length,
      Array.from(document.querySelectorAll('.note-type-sec .rte-editor')).filter(el=>el.getClientRects().length).length
    ]`);
    assert.deepEqual(visible,[88,5]);
    await page.eval('toggleBarNumbers()');
    assert.equal(await page.eval("Array.from(document.querySelectorAll('#sheet .bar-num')).filter(el=>el.getClientRects().length).length"),88);
    await page.eval('toggleBarNumbers()');
    assert.equal(await page.eval('hasUnsavedChanges()'),false);
  }
  async function openPickers(page) {
    await page.eval(`(() => {
      const cell = document.querySelector('.bar-cell');
      openRhythmPicker(0,0,cell);
      openColorPicker(0,document.querySelector('.section-tag'),{stopPropagation(){}});
    })()`);
    assert.equal(await page.eval("document.querySelector('#rhythmPicker').classList.contains('open')"),true);
    assert.ok(await page.eval("document.querySelectorAll('#swatches .swatch').length")>0);
    await page.eval('closeAllRhythmPopups();closeColorPicker()');
  }
  async function assertPickersRebuilt(page) {
    assert.ok(await page.eval("document.querySelectorAll('#rhythmPicker .picker-item').length")>0);
    assert.ok(await page.eval("document.querySelectorAll('#bpNotes .beat-picker-item').length")>0);
    await openPickers(page);
  }

  let browserAgent;
  if (hysteriaRevision) {
    const hysteria = await open('hysteria-review.html',1280,900);
    browserAgent = await hysteria.eval('navigator.userAgent');
    const original = await readRevision(hysteria);
    assert.deepEqual(original.stored,hysteriaRevision);
    assert.equal(original.live.sheetMeta.revisionHash,'0dbbc4d73396c42b8226f136c80cc425238242516c625b10a58d8126116300fa');
    await click(hysteria,'#edit-btn');
    await openPickers(hysteria);
    const unchangedFile = await download(hysteria,'hysteria-review.html');
    const unchanged = await open(unchangedFile.path,390,844);
    assert.deepEqual(await readRevision(unchanged),original);
    assert.equal(original.live.dom.reduce((n,s)=>n+s.bars.length,0),88);
    assert.equal(original.live.dom.filter(s=>s.lyrics.length).length,5);
    await assertBothViews(unchanged);
    fileSizes.hysteria = {generated:(await fs.stat(path.join(root,'hysteria-review.html'))).size,downloaded:unchangedFile.bytes.length};
    assert.ok(fileSizes.hysteria.downloaded <= fileSizes.hysteria.generated + 1024, 'unexpected export size growth');
    cases.push('Exact Hysteria revision downloads, reopens with 88 bars and 5 lyric blocks, and switches Both/Band/Vocal');
    await click(unchanged,'#edit-btn');
    await assertPickersRebuilt(unchanged);
    const repeatedHysteria = await download(unchanged,'hysteria-review.html');
    assert.ok(repeatedHysteria.bytes.equals(unchangedFile.bytes), 'unchanged Hysteria re-export changed HTML bytes');
    const originalLyricText = await unchanged.eval("document.querySelector('.rte-editor').textContent");
    const word = originalLyricText.match(/^\S+/)[0];
    await selectWord(unchanged, word.length);
    await applyFormatting(unchanged);
    const editedFile = await download(unchanged,'hysteria-review.html');
    const edited = await open(editedFile.path,390,844);
    assertFormat(await readFormatting(edited, word));
    assert.equal(await edited.eval("document.querySelector('.rte-editor').textContent"),originalLyricText);
    const editedRevision = await readRevision(edited);
    assert.equal(editedRevision.stored.contentRevision,hysteriaRevision.contentRevision+1);
    assert.equal(editedRevision.stored.provenance.parentRevisionHash,original.live.sheetMeta.revisionHash);
    assertOnlyFormattedLyric(editedRevision.stored,hysteriaRevision);
    cases.push('Hysteria B/I/U survives a real download and reopen, with only the selected lyric formatting changed');
  }

  const editable = await open('synthetic-review.html',1280,900);
  const fixtureBefore = await readRevision(editable);
  assert.deepEqual(fixtureBefore.stored,fixture);
  const fixtureLyricText = await editable.eval("document.querySelector('.rte-editor').textContent");
  await click(editable,'#edit-btn');
  await selectWord(editable, 9);
  await applyFormatting(editable);
  assertFormat(await readFormatting(editable, 'Synthetic'));
  await click(editable,'.lyric-underline');
  const withoutUnderline = await readFormatting(editable, 'Synthetic');
  assert.ok(withoutUnderline && withoutUnderline.weight>=700);
  assert.equal(withoutUnderline.italic,'italic');
  assert.equal(withoutUnderline.underlined,false);
  await click(editable,'.lyric-underline');
  assertFormat(await readFormatting(editable, 'Synthetic'));
  assert.equal(await editable.eval('hasUnsavedChanges()'),true);
  const formattedFile = await download(editable,'contract-fixture-review.html');
  const formatted = await open(formattedFile.path,390,844);
  const formattedRevision = await readRevision(formatted);
  assertFormat(await readFormatting(formatted, 'Synthetic'));
  assert.equal(formattedRevision.stored.contentRevision,fixture.contentRevision+1);
  assert.equal(formattedRevision.stored.provenance.parentRevisionHash,fixtureBefore.live.sheetMeta.revisionHash);
  assertOnlyFormattedLyric(formattedRevision.stored,fixture);
  assert.equal(await formatted.eval("document.querySelector('.rte-editor').textContent"),
      fixtureLyricText);
  cases.push('B/I/U apply to selected synthetic lyric text and survive Save HTML and reopen');
  await click(formatted,'#edit-btn');
  const repeatedFile = await download(formatted,'contract-fixture-review.html');
  const repeated = await open(repeatedFile.path,1280,900);
  assert.deepEqual(await readRevision(repeated),formattedRevision);
  assert.equal(repeatedFile.bytes.length,formattedFile.bytes.length);
  assert.ok(repeatedFile.bytes.equals(formattedFile.bytes), 'unchanged fixture re-export changed HTML bytes');
  cases.push('Unchanged re-export preserves exact draft revision, HTML bytes and file size');

  const blank = await open(template,390,844);
  await click(blank,'#edit-btn');
  await blank.eval(`(() => {
    const title=document.getElementById('tb-filename');
    title.value='Local Blank Test';
    title.dispatchEvent(new Event('input',{bubbles:true}));
  })()`);
  const blankFile = await download(blank,'local-blank-test-review.html');
  const reopenedBlank = await open(blankFile.path,390,844);
  assert.equal(await reopenedBlank.eval("document.getElementById('tb-filename').value"),'Local Blank Test');
  assert.equal(await reopenedBlank.eval('document.body.dataset.performanceView'),'both');
  assert.equal(await reopenedBlank.eval('SECTIONS[0].bars.length'),4);
  await click(reopenedBlank,'#edit-btn');
  await assertPickersRebuilt(reopenedBlank);
  await reopenedBlank.eval("openRhythmPicker(0,0,document.querySelector('.bar-cell'))");
  // Luminous keeps rhythm controls hidden in review. Exercise the retained
  // handlers without changing the existing visibility policy.
  assert.equal(await reopenedBlank.eval("getComputedStyle(document.getElementById('rhythmPicker')).display"),'none');
  await reopenedBlank.eval("document.querySelector('#rhythmPicker .picker-item').click()");
  assert.ok(await reopenedBlank.eval('SECTIONS[0].bars[0].r.length')>0);
  await reopenedBlank.eval("openBeatPicker(0,0,0,document.querySelector('.beat-slot'))");
  const beat = await reopenedBlank.eval("document.querySelectorAll('#bpNotes .beat-picker-item')[1].dataset.id");
  assert.equal(await reopenedBlank.eval("getComputedStyle(document.getElementById('beatPicker')).display"),'none');
  await reopenedBlank.eval("document.querySelector('#bpNotes .beat-picker-item:nth-child(2)').click()");
  assert.equal(await reopenedBlank.eval('SECTIONS[0].bars[0].r[0]'),beat);
  await reopenedBlank.eval("openColorPicker(0,document.querySelector('.section-tag'),{stopPropagation(){}})");
  const beforeColor = await reopenedBlank.eval('SECTIONS[0].color.bar');
  await click(reopenedBlank,'#swatches .swatch:nth-child(2)');
  assert.notEqual(await reopenedBlank.eval('SECTIONS[0].color.bar'),beforeColor);
  cases.push('Blank template downloads and reopens with entered metadata, four bars and Both; color UI and hidden rhythm/beat handlers still apply options');
  for (const page of clients) assert.deepEqual(page.errors,[]);
  const result={status:'pass',cases,browser:browserAgent || await editable.eval('navigator.userAgent'),fileSizes};
  console.log(JSON.stringify(result,null,2));
  passed = true;
} finally {
  for (const session of clients) session.ws.close();
  if (browser.exitCode === null && browser.signalCode === null) {
    const closed = once(browser, 'close');
    browser.kill();
    await closed;
  }
  if (passed) await fs.rm(root, {recursive: true, force: true});
  else console.error('Browser test artifacts:', root);
}
