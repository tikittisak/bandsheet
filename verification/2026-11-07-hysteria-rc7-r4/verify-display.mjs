import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { readFileSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { runInNewContext } from 'node:vm';

const root = process.argv[2] || path.dirname(fileURLToPath(import.meta.url));
const read = file => readFileSync(path.join(root, file), 'utf8');
const hash = file => createHash('sha256').update(readFileSync(path.join(root, file))).digest('hex');
const song = read('review/song.html');
const index = read('review/index.html');
const decision = JSON.parse(read('decision.json'));
const data = JSON.parse(song.match(/<script id="bandsheet-review-data" type="application\/json">([^]*?)<\/script>/)[1]);
assert.match(song, /<html lang="en"/);
assert.match(index, /<html lang="en"/);
assert.deepEqual(JSON.parse(read('review/catalog.json')).songs, [
  { title: 'Hysteria', href: 'song.html', review: data.review },
]);
assert.equal(decision.revisionHash, data.review.revisionHash);
assert.equal(decision.approvedAt, data.review.approvedAt);
assert.equal(data.revision.contentRevision, 4);
const elements = Object.fromEntries(['review-status', 'review-edited', 'review-approved'].map(id => {
  assert.ok(song.includes('id="' + id + '"'));
  return [id, { dataset: {} }];
}));
const context = {
  BandsheetReview: { data },
  document: { getElementById: id => elements[id] },
  currentSheetSignature: () => 'unchanged',
  hasUnsavedChanges: () => false,
};
const timeline = song.slice(song.indexOf('const REVIEW_MONTHS ='), song.indexOf('let lastLocalExport;'));
const statusUpdate = song.slice(song.indexOf('function updateSaveState(){'), song.indexOf('function markSheetSaved(){'));
runInNewContext(timeline + statusUpdate + 'updateSaveState();', context, { timeout: 1000 });
assert.equal(elements['review-status'].dataset.state, 'approved');
const indexRow = index.match(/<article>\s*<a href="song\.html">Hysteria<\/a>\s*<p class="status">([^<]+)<\/p>\s*<p>([^<]+)<\/p>\s*<p>([^<]+)<\/p>\s*<\/article>/);
const displayed = Object.values(elements).map(element => element.textContent);
assert.deepEqual(displayed, indexRow.slice(1));
assert.deepEqual(displayed, ['Approved · r4', 'Last edited: 7 Nov 2026, 14:19 ICT', 'Approved on: 7 Nov 2026, 14:20 ICT']);
console.log(JSON.stringify({
  method: 'Generated index HTML compared with the generated song page’s status and timeline JavaScript executed in Node with a minimal DOM stub.',
  browserPreview: 'Unavailable: browser policy blocked direct file URL navigation.',
  nodeVersion: process.version,
  revisionHash: data.review.revisionHash,
  parentRevisionHash: data.revision.provenance.parentRevisionHash,
  approvedAt: decision.approvedAt,
  approvedAtSource: 'Local ICT clock sampled immediately after receiving Ti’s approval; not a chat-service timestamp.',
  sheet: displayed,
  index: indexRow.slice(1),
  filesSha256: Object.fromEntries([
    'hysteria-rc7-r4.html', 'decision.json', 'review/song.html', 'review/index.html', 'review/catalog.json'
  ].map(file => [file, hash(file)])),
}, null, 2));
