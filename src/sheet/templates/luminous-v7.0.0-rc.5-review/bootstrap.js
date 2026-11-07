/* Snapshot the static shell before executing the application scripts. */
(() => {
  const slotId = 'bandsheet-review-data';
  const slot = document.getElementById(slotId);
  const data = JSON.parse(slot.textContent);
  const payload = data.revision || data.draft;
  if (data.format !== 'bandsheet-review-html-1' || !payload || !data.sheetMeta ||
      Boolean(data.revision) === Boolean(data.draft)) throw Error('Invalid review data');

  const shell = '<!doctype html>\n' + document.documentElement.outerHTML;
  const tag = '<script id="' + slotId + '" type="application/json">';
  const offset = shell.indexOf(tag);
  const start = offset + tag.length;
  const end = shell.indexOf('</' + 'script>', start);
  if (offset < 0 || end < 0 || shell.indexOf(tag, start) !== -1) {
    throw Error('Review data slot is missing or ambiguous');
  }

  const pin = data.shellSha256;
  const shellBytes = new TextEncoder().encode(shell.slice(0, start) + shell.slice(end));
  let shellCheck;
  const metaIds = {
    title: 'tb-filename', artist: 'tb-artist', key: 'meta-key',
    bpm: 'meta-bpm', timeSignature: 'meta-time', vocalist: 'meta-vocalist'
  };
  window.BandsheetReview = {
    data, payload, metaIds,
    async htmlWithData(next) {
      shellCheck ||= crypto.subtle.digest('SHA-256', shellBytes).then(hash =>
        Array.from(new Uint8Array(hash), byte => byte.toString(16).padStart(2, '0')).join(''));
      if (await shellCheck !== pin) throw Error('UI shell differs from the pinned template');
      const escapes = {'<': '\\u003c', '>': '\\u003e', '&': '\\u0026'};
      const json = JSON.stringify(next).replace(/[<>&]/g, character => escapes[character]);
      return shell.slice(0, start) + json + shell.slice(end);
    }
  };
  for (const [key, id] of Object.entries(metaIds)) {
    document.getElementById(id).value = payload.metadata[key];
  }
  if (payload.metadata.title) document.title = payload.metadata.title + ' · Bandsheet';

  for (const source of document.querySelectorAll('script[type="application/x-bandsheet-js"]')) {
    const active = document.createElement('script');
    active.textContent = source.textContent;
    source.after(active);
    active.remove();
  }
})();
