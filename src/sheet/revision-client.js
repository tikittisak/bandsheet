/* Synthetic JSON/Git adapter. Frozen Luminous files are never edited. */
(function () {
  'use strict';
  function canonical(value) {
    const utf8 = new TextEncoder();
    function string(s) {
      for (let i=0;i<s.length;i++) {
        const n=s.charCodeAt(i);
        if (n>=0xd800 && n<=0xdbff) { const next=s.charCodeAt(++i); if (!(next>=0xdc00 && next<=0xdfff)) throw Error('Unpaired surrogate'); }
        else if (n>=0xdc00 && n<=0xdfff) throw Error('Unpaired surrogate');
      }
      return s;
    }
    function order(a,b) { const x=utf8.encode(a),y=utf8.encode(b); for(let i=0;i<Math.min(x.length,y.length);i++){if(x[i]!==y[i])return x[i]-y[i];} return x.length-y.length; }
    function tag(v) {
      if(v===null)return ['null'];
      if(typeof v==='boolean')return ['boolean',v];
      if(typeof v==='string')return ['string',string(v)];
      if(typeof v==='number'){
        if(!Number.isFinite(v)||(Number.isInteger(v)&&!Number.isSafeInteger(v)))throw Error('Number outside portable JSON domain');
        const bytes=new Uint8Array(8);new DataView(bytes.buffer).setFloat64(0,v===0?0:v,false);
        return ['number',Array.from(bytes,b=>b.toString(16).padStart(2,'0')).join('')];
      }
      if(Array.isArray(v))return ['array',v.map(tag)];
      if(v && Object.getPrototypeOf(v)===Object.prototype)return ['object',Object.keys(v).map(string).sort(order).map(k=>[k,tag(v[k])])];
      throw Error('Not a JSON value');
    }
    return JSON.stringify(tag(value));
  }
  async function hash(value) { const bytes=await crypto.subtle.digest('SHA-256',new TextEncoder().encode(canonical(value)));return Array.from(new Uint8Array(bytes),b=>b.toString(16).padStart(2,'0')).join(''); }
  function semantic(r){return {metadata:r.metadata,sections:r.sections,footer:r.footer,settings:r.settings,extensions:r.extensions||{}};}
  const clone=x=>JSON.parse(JSON.stringify(x));
  globalThis.RevisionProtocol={canonical,hash,semantic};
  if(typeof document==='undefined')return;
  const embedded=document.getElementById('bandsheet-revision');if(!embedded)return;
  let base=JSON.parse(embedded.textContent), pending=null, saving=false, state='loaded-unverified';
  const ids={title:'tb-filename',artist:'tb-artist',key:'meta-key',bpm:'meta-bpm',timeSignature:'meta-time',vocalist:'meta-vocalist'};
  const config=globalThis.BANDSHEET_WRITER||null;
  const recoveryPrefix='bandsheet-draft-v1:'+base.songId+':';
  // A tab owns its cache entry. Two tabs must never overwrite each other's draft.
  // Fresh identity per page instance, including browser "duplicate tab".
  const sessionId=crypto.randomUUID();
  const recoveryKey=recoveryPrefix+sessionId;
  function payload(){return {metadata:Object.fromEntries(Object.entries(ids).map(([key,id])=>[key,document.getElementById(id).value])),sections:clone(SECTIONS),footer:clone(FOOTER),settings:clone(SETTINGS),extensions:clone(base.extensions||{})};}
  function status(message){const el=document.getElementById('save-state');if(el){el.textContent=message;el.dataset.persistence=state;el.classList.toggle('dirty',hasUnsavedChanges());}}
  function remember(){try{localStorage.setItem(recoveryKey,JSON.stringify({baseRevision:base,payload:payload(),pending}));return true;}catch(e){return false;}}
  function apply(p){for(const [key,id] of Object.entries(ids))document.getElementById(id).value=p.metadata[key];SECTIONS=clone(p.sections);FOOTER=clone(p.footer);SETTINGS=clone(p.settings);render();}
  window.hasUnsavedChanges=()=>canonical(payload())!==canonical(semantic(base));
  window.markSheetSaved=()=>{}; // A download or DOM signature cannot acknowledge persistence.
  window.updateSaveState=function(){if(saving)return;if(hasUnsavedChanges()){state='dirty';status(remember()?'Unsaved draft — local recovery only':'Unsaved draft — local recovery unavailable');}};
  async function send(request){
    if(!config)throw Error('No writer connected; export is not a Git save');
    const response=await fetch('/api/save',{method:'POST',headers:{'Content-Type':'application/json','X-Bandsheet-Token':config.token},body:JSON.stringify(request)});
    const result=await response.json();
    if(!response.ok)throw Error(result.error||'Save failed');
    const r=result.revision;
    if(r.songId!==base.songId||await hash(r)!==result.revisionHash||await hash(semantic(r))!==result.contentHash||canonical(semantic(r))!==canonical(request.payload))throw Error('Receipt/payload integrity mismatch');
    if(result.changed && r.provenance.parentRevisionHash!==request.expectedParentHash)throw Error('Receipt parent mismatch');
    if(result.persistence!=='verified-test-remote')throw Error('Unknown persistence authority');
    base=clone(r);embedded.textContent=JSON.stringify(base);pending=null;
    SHEET_META.contentRevision=r.contentRevision;SHEET_META.sheetRevision=r.contentRevision;
    SHEET_META.contentHash=result.contentHash;SHEET_META.revisionHash=result.revisionHash;SHEET_META.parentRevisionHash=r.provenance.parentRevisionHash;
    state='verified-test-remote';remember();status('Saved to TEST Git remote — not GitHub / not approved');
    return result;
  }
  window.saveToFile=async function(){
    if(saving)return; saving=true;state='saving';status('Saving — awaiting Git receipt');
    try{
      if(!pending)pending={saveId:crypto.randomUUID(),songId:base.songId,expectedParentHash:await hash(base),payload:payload()};
      remember();const result=await send(pending);return result;
    }catch(error){state='pending-or-conflict';const cached=remember();status(error.message+' — not acknowledged; '+(cached?'retry preserves save ID':'recovery cache unavailable'));return {error:error.message};}
    finally{saving=false;if(!pending&&hasUnsavedChanges())updateSaveState();}
  };
  window.exportRevisionRecovery=function(){
    remember();const bundle={format:'bandsheet-recovery-1',baseRevision:base,payload:payload(),pending};
    const a=document.createElement('a');a.href=URL.createObjectURL(new Blob([JSON.stringify(bundle)],{type:'application/json'}));a.download=base.songId+'-recovery.json';a.click();setTimeout(()=>URL.revokeObjectURL(a.href),1000);
    status('Recovery export requested — not a Git save');
  };
  window.bandsheetRevisionState=()=>({base:clone(base),payload:payload(),pending:clone(pending),state,saving});
  function recover(entry){
    if(canonical(entry.baseRevision)===canonical(base)){pending=entry.pending;apply(entry.payload);state=hasUnsavedChanges()||pending?'recovered-local':'loaded-unverified';}
    else {state='recovery-conflict';throw Error('Recovery belongs to another revision; retained without applying');}
  }
  window.listRevisionRecovery=function(){
    const records=[];
    for(let i=0;i<localStorage.length;i++){
      const key=localStorage.key(i);if(!key.startsWith(recoveryPrefix))continue;
      try{const entry=JSON.parse(localStorage.getItem(key));if(entry.pending||canonical(entry.payload)!==canonical(semantic(entry.baseRevision)))records.push({key,entry});}catch(error){records.push({key,unreadable:true});}
    }
    return records;
  };
  window.restoreRevisionRecovery=function(key){if(!key.startsWith(recoveryPrefix))throw Error('Wrong song recovery');recover(JSON.parse(localStorage.getItem(key)));remember();status('Recovered local draft — not a Git save');};
  try{
    const own=JSON.parse(localStorage.getItem(recoveryKey)||'null');
    const candidates=listRevisionRecovery();
    if(own)recover(own);
    else if(candidates.length===1&&!candidates[0].unreadable&&canonical(candidates[0].entry.baseRevision)===canonical(base))recover(candidates[0].entry);
    else if(candidates.length)state='recovery-selection-required';
  }catch(error){if(state!=='recovery-conflict')state='recovery-unreadable';}
  status(state==='recovered-local'?'Recovered local draft — not saved':state.startsWith('recovery-')?'Local drafts need explicit recovery review — none overwritten':'Synthetic review — persistence not yet verified');
  const button=document.createElement('button');button.className='tb-btn ghost';button.textContent='export recovery JSON';button.onclick=exportRevisionRecovery;document.getElementById('toolbar').appendChild(button);
  if(state==='recovery-selection-required'){
    const select=document.createElement('select');select.setAttribute('aria-label','Local draft to recover');
    const blank=document.createElement('option');blank.textContent='Choose local draft';blank.value='';select.appendChild(blank);
    for(const record of listRevisionRecovery()){const option=document.createElement('option');option.value=record.key;option.textContent=record.unreadable?'Unreadable draft':record.entry.payload.metadata.title+' · '+record.key.slice(-8);select.appendChild(option);}
    select.onchange=()=>{try{restoreRevisionRecovery(select.value);}catch(error){status(error.message);}};document.getElementById('toolbar').appendChild(select);
  }
})();
