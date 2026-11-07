/* Local review editor. The browser downloads a draft without contacting a writer. */
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

  function format(command) {
    if (!EDIT_MODE) return;
    rememberSelection();
    editor.focus({preventScroll: true});
    const selection = window.getSelection();
    if (savedRange && editor.contains(savedRange.commonAncestorContainer)) {
      selection.removeAllRanges();
      selection.addRange(savedRange);
    }
    document.execCommand('styleWithCSS', false, false);
    const before = editor.innerHTML;
    document.execCommand(command);
    if (editor.innerHTML !== before) editor.dispatchEvent(new Event('input', {bubbles: true}));
    rememberSelection();
  }

  for (const [command, label, title] of [
    ['bold', 'B', 'Bold'], ['italic', 'I', 'Italic'], ['underline', 'U', 'Underline']
  ]) {
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

  editor.addEventListener('blur', rememberSelection);
  toolbar.addEventListener('pointerdown', rememberSelection);
  return toolbar;
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
    const {data, metaIds, htmlWithData} = window.BandsheetReview;
    const base = data.revision || null;
    const payload = JSON.parse(JSON.stringify({
      metadata: Object.fromEntries(Object.entries(metaIds).map(([key, id]) => [key, document.getElementById(id).value])),
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

    const next = {...data, sheetMeta, ...(revision ? {revision} : {draft: payload})};
    const blob = new Blob([await htmlWithData(next)], {type: 'text/html;charset=utf-8'});
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
