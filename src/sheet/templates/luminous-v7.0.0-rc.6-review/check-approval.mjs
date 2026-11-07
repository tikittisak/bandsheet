import assert from 'node:assert/strict';
import { spawn, spawnSync } from 'node:child_process';
import fs from 'node:fs/promises';
import { once } from 'node:events';
import os from 'node:os';
import path from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

const [hysteria, approvedFixture] = process.argv.slice(2).map(value => path.resolve(value));
assert.ok(hysteria && approvedFixture, 'Pass the Hysteria and synthetic approval bundle directories');
const root = await fs.mkdtemp(path.join(os.tmpdir(),'bandsheet-approval-test-'));
const temp = path.join(root,'profile');
const build = fileURLToPath(new URL('./build.py',import.meta.url));
const verify = (...args) => spawnSync('python3',['-B',build,'--verify',...args],{encoding:'utf8'});
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
    return s;
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

  async function inspect(bundle, expected) {
    const index = await open(path.join(bundle,'index.html'),390,844);
    const song = await open(path.join(bundle,'song.html'),390,844);
    const label = await song.eval("document.querySelector('#review-status').textContent");
    assert.equal(label, expected);
    assert.equal(await index.eval("document.querySelector('.status').textContent"), label);
    assert.equal(await index.eval("document.querySelector('article a').getAttribute('href')"), 'song.html');
    assert.equal(await song.eval("document.documentElement.lang"),'en');
    assert.equal(await index.eval("document.documentElement.lang"),'en');
    return {index,song};
  }
  const pending = await inspect(hysteria, 'Pending review · r2');
  assert.equal(await pending.song.eval('document.querySelectorAll("#sheet .bar-cell[data-bi]").length'),88);
  const {index,song} = await inspect(approvedFixture,'Approved (test) · r1 · 2026-11-07T12:00:00+07:00');
  assert.notEqual(verify(path.join(approvedFixture,'song.html')).status, 0);
  await click(song,'#edit-btn');
  await song.eval(`(() => {
    const input = document.getElementById('tb-filename');
    input.value = 'Contract Fixture Changed';
    input.dispatchEvent(new Event('input',{bubbles:true}));
  })()`);
  assert.equal(await song.eval("document.querySelector('#review-status').textContent"),'Draft · unsaved changes');
  await song.call('Browser.setDownloadBehavior',{behavior:'allow',downloadPath:root});
  await click(song,'#local-save-html-btn');
  const file = path.join(root,'contract-fixture-changed-rc6-r2.html');
  await waitFor(async () => (await fs.stat(file)).size > 0, await song.eval("document.getElementById('save-state').textContent"));
  const downloaded = await open(file,390,844);
  assert.equal(await downloaded.eval("document.querySelector('#review-status').textContent"),'Draft · r2');
  assert.equal(await downloaded.eval('BandsheetReview.data.review.approvedAt'),null);
  assert.equal(await index.eval("document.querySelector('.status').textContent"),'Approved (test) · r1 · 2026-11-07T12:00:00+07:00');
  const proof = verify(file);
  assert.equal(proof.status,0,proof.stderr);
  for (const page of clients) assert.deepEqual(page.errors,[]);
  passed = true;
  console.log(JSON.stringify({status:'pass',cases:[
    'Hysteria r2 and linked index show Pending review',
    'Synthetic sheet and index show the same Approved test timestamp',
    'Export after an edit reopens as Draft r2, while the index still shows approved r1',
    'Standalone verifier rejects an approved file without its external decision'
  ]},null,2));
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
