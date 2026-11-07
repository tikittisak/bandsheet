/* Local review editor. The browser downloads a draft without contacting a writer. */
const LOCAL_META_IDS = {
  title: 'tb-filename', artist: 'tb-artist', key: 'meta-key',
  bpm: 'meta-bpm', timeSignature: 'meta-time', vocalist: 'meta-vocalist'
};

function makeLyricFormatToolbar(editor) {
  const toolbar = document.createElement('div');
  toolbar.className = 'rte-toolbar lyric-format-toolbar';
  toolbar.setAttribute('role', 'group');
  toolbar.setAttribute('aria-label', 'Lyric formatting');
  let savedRange;

  function rememberSelection() {
    const selection = window.getSelection();
    if (selection.rangeCount && editor.contains(selection.getRangeAt(0).commonAncestorContainer)) {
      savedRange = selection.getRangeAt(0).cloneRange();
    }
  }

  function format(command, value = null) {
    if (!EDIT_MODE) return;
    rememberSelection();
    editor.focus({preventScroll: true});
    const selection = window.getSelection();
    if (savedRange && editor.contains(savedRange.commonAncestorContainer)) {
      selection.removeAllRanges();
      selection.addRange(savedRange);
    }
    document.execCommand('styleWithCSS', false, false);
    document.execCommand(command, false, value);
    editor.dispatchEvent(new Event('input', {bubbles: true}));
    rememberSelection();
  }

  for (const [command, label, title] of [['bold', 'B', 'Bold'], ['italic', 'I', 'Italic']]) {
    const button = document.createElement('button');
    button.type = 'button';
    button.className = 'rte-btn lyric-' + command;
    button.textContent = label;
    button.title = title;
    button.setAttribute('aria-label', title);
    button.addEventListener('mousedown', event => event.preventDefault());
    button.addEventListener('click', () => format(command));
    toolbar.appendChild(button);
  }

  const fonts = document.createElement('select');
  fonts.className = 'rte-btn';
  fonts.setAttribute('aria-label', 'Lyric font');
  fonts.appendChild(new Option('Font', '', true, true));
  fonts.options[0].disabled = true;
  for (const name of ['Arial', 'Georgia', 'Courier New', 'Roboto Condensed']) {
    fonts.appendChild(new Option(name, name));
  }
  fonts.addEventListener('change', () => {
    format('fontName', fonts.value);
    fonts.selectedIndex = 0;
  });
  toolbar.appendChild(fonts);
  for (const event of ['pointerup', 'keyup', 'blur']) editor.addEventListener(event, rememberSelection);
  toolbar.addEventListener('pointerdown', rememberSelection);
  return toolbar;
}

function localInlineJSON(value) {
  const escapes = {'<': '\\u003c', '>': '\\u003e', '&': '\\u0026'};
  return JSON.stringify(value).replace(/[<>&]/g, character => escapes[character]);
}

function replaceLocalBlock(script, name, marker, value) {
  const pattern = new RegExp('^var ' + name + ' = [\\s\\S]*?;\\r?\\n// ── END ' + marker + ' ──$', 'gm');
  if (Array.from(script.matchAll(pattern)).length !== 1) throw Error('Missing or ambiguous ' + name);
  return script.replace(pattern, () => 'var ' + name + ' = ' + localInlineJSON(value) + ';\n// ── END ' + marker + ' ──');
}

let lastLocalExport;

function localExportStatus() {
  return lastLocalExport?.signature === currentSheetSignature() ? lastLocalExport.message : '';
}

async function exportLocalReviewHtml() {
  const button = document.getElementById('local-save-html-btn');
  if (button.disabled) return;
  button.disabled = true;
  const signature = currentSheetSignature();
  try {
    const embedded = document.getElementById('bandsheet-revision');
    const base = embedded ? JSON.parse(embedded.textContent) : null;
    const payload = JSON.parse(JSON.stringify({
      metadata: Object.fromEntries(Object.entries(LOCAL_META_IDS).map(([key, id]) => [key, document.getElementById(id).value])),
      sections: SECTIONS, footer: FOOTER, settings: SETTINGS, extensions: base?.extensions || {}
    }));
    const sheetMeta = {...SHEET_META};
    let revision = base;
    if (base) {
      const protocol = globalThis.RevisionProtocol;
      const baseHash = await protocol.hash(base);
      if (sheetMeta.revisionHash !== baseHash) throw Error('Source revision hash mismatch');
      if (protocol.canonical(protocol.semantic(base)) !== protocol.canonical(payload)) {
        revision = {
          ...base, ...payload, contentRevision: base.contentRevision + 1,
          provenance: {
            sourceType: 'local-html-draft',
            capturedOn: new Date().toISOString().slice(0, 10),
            parentRevisionHash: baseHash,
            sourceRef: base.provenance.sourceRef || '',
            note: 'Local HTML draft from the review editor.'
          }
        };
      }
      Object.assign(sheetMeta, {
        contentRevision: revision.contentRevision, sheetRevision: revision.contentRevision,
        contentUpdated: revision.provenance.capturedOn, contentSource: revision.provenance.sourceType,
        parentRevisionHash: revision.provenance.parentRevisionHash,
        revisionHash: await protocol.hash(revision), contentHash: await protocol.hash(protocol.semantic(revision))
      });
    } else if (hasUnsavedChanges()) {
      sheetMeta.sheetRevision = (Number(sheetMeta.sheetRevision) || 1) + 1;
      sheetMeta.contentUpdated = new Date().toISOString().slice(0, 10);
      sheetMeta.contentSource = 'local-html-draft';
    }

    const copy = document.documentElement.cloneNode(true);
    copy.removeAttribute('style');
    copy.querySelector('body').className = 'view-mini';
    copy.querySelector('#sheet').replaceChildren();
    copy.querySelector('#focus-return')?.remove();
    copy.querySelector('#toast')?.classList.remove('show');
    copy.querySelector('#local-save-html-btn').removeAttribute('disabled');
    copy.querySelector('#save-state').textContent = 'Local HTML draft';
    for (const [key, id] of Object.entries(LOCAL_META_IDS)) {
      copy.querySelector('#' + id).setAttribute('value', payload.metadata[key]);
    }
    copy.querySelector('title').textContent = (payload.metadata.title || 'Bandsheet') + ' · Bandsheet';
    const data = copy.querySelector('#bandsheet-sheet-data');
    let script = data.textContent;
    for (const [name, marker, value] of [
      ['SECTIONS', 'DATA', payload.sections], ['FOOTER', 'FOOTER', payload.footer],
      ['SETTINGS', 'SETTINGS', payload.settings], ['SHEET_META', 'SHEET META', sheetMeta]
    ]) script = replaceLocalBlock(script, name, marker, value);
    data.textContent = script;
    if (revision) copy.querySelector('#bandsheet-revision').textContent = localInlineJSON(revision);

    const blob = new Blob(['<!doctype html>\n', copy.outerHTML], {type: 'text/html;charset=utf-8'});
    const link = document.createElement('a');
    const url = URL.createObjectURL(blob);
    link.href = url;
    link.download = filenameSlug(payload.metadata.title) + '-review.html';
    document.body.appendChild(link);
    link.click();
    link.remove();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
    lastLocalExport = {signature, message: 'HTML download requested · check Downloads'};
  } catch (error) {
    lastLocalExport = {signature, message: 'HTML export failed: ' + error.message};
  } finally {
    button.disabled = false;
    updateSaveState();
  }
}
