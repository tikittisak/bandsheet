#!/usr/bin/env python3
"""Build a local review sheet and index from one exact revision and review record."""
import argparse
from datetime import datetime
from hashlib import sha256
from html import escape
import json
from pathlib import Path
import re
import runpy

FOLDER = Path(__file__).resolve().parent
BASE_FOLDER = FOLDER.with_name('luminous-v7.0.0-rc.5-review')
BASE = runpy.run_path(str(BASE_FOLDER / 'build.py'))
BASE_SHA = 'f813344b24b67f76e3e41b4d334dd742dc7a537f7ccd7872df299c79a6c5e5ff'
VERSION = '7.0.0-rc.6-review'
contract = BASE['contract']
split_slot = BASE['split_slot']
inline_data = BASE['inline_data']
shell_hash = BASE['shell_hash']
check_shell = BASE['check_shell']

ENGLISH = {
    'เพิ่ม lyrics column แล้ว': 'Lyric column added',
    'ลบ lyrics column 2 ?': 'Delete lyric column 2?',
    'ลดเป็น 1 column แล้ว': 'One lyric column remaining',
    'เพิ่ม ': 'Added ',
    ' ห้องแล้ว': ' bars',
    'ต้องมีอย่างน้อย 1 ห้อง': 'At least one bar is required',
    'ลบ ': 'Delete ',
    'สลับห้องแล้ว ✓': 'Bar moved',
    'renumber เรียบร้อย': 'Bars renumbered',
    'เพิ่ม section แล้ว': 'Section added',
    'เพิ่ม note section แล้ว': 'Note section added',
    'ย้าย section ขึ้น ✓': 'Section moved up',
    'ย้าย section ลง ✓': 'Section moved down',
    'ต้องมีอย่างน้อย 1 section': 'At least one section is required',
    'ลบ section แล้ว ✓': 'Section deleted',
    'reset section แล้ว ✓': 'Section reset',
    'duplicate section แล้ว ✓': 'Section duplicated',
    'ไม่มี section ถัดไป': 'No next section',
    'ไม่มี section ก่อนหน้า': 'No previous section',
    'ถึงท้ายหน้าแล้ว': 'End of sheet',
    'ใส่ duration เพื่อความแม่นยำ': 'Set a duration for more accurate scrolling',
    'จบเพลงแล้ว ✓': 'End of song',
}


def replace_once(text, old, new):
    if text.count(old) != 1:
        raise ValueError(f'Unexpected template anchor: {old[:70]!r}')
    return text.replace(old, new, 1)


def review_projection(revision, state, decision=None):
    digest = contract.revision_hash(revision) if revision else None
    number = revision['contentRevision'] if revision else 1
    result = {'state': state, 'revisionHash': digest, 'approvedAt': None, 'test': False}
    if decision:
        result.update(approvedAt=decision['approvedAt'], test=decision['scope'] == 'synthetic-test')
    result['label'] = {
        'draft': 'Draft', 'pending': 'Pending review',
        'approved': 'Approved (test)' if result['test'] else 'Approved',
    }[state] + f' · r{number}'
    if result['approvedAt']:
        result['label'] += ' · ' + result['approvedAt']
    return result


def render_template():
    raw = (BASE_FOLDER / 'template.html').read_bytes()
    if sha256(raw).hexdigest() != BASE_SHA or BASE['render_template']() != raw:
        raise ValueError('Pinned rc.5 template differs')
    prefix, slot, suffix = split_slot(raw)
    data = contract.parse_json(slot.decode())
    source = (prefix + suffix).decode().replace(BASE['VERSION'], VERSION)
    source = replace_once(source, 'lang="th"', 'lang="en"')
    for old in sorted(ENGLISH, key=len, reverse=True):
        if old not in source:
            raise ValueError(f'Missing UI translation anchor: {old!r}')
        source = source.replace(old, ENGLISH[old])
    source = source.replace("toast('Delete '+remove+' bars')", "toast('Removed '+remove+' bars')")
    if re.search(r'[\u0e00-\u0e7f]', source):
        raise ValueError('Untranslated interface text')
    source = replace_once(source, '<div id="sheet"></div>',
        '<div id="review-status" role="status" class="review-status">Draft</div>\n<div id="sheet"></div>')
    source = replace_once(source, '/* Both follows the existing section pairs',
        '.review-status{padding:6px 12px;color:#42546e;font:600 12px system-ui;overflow-wrap:anywhere}\n'
        '.review-status[data-state="approved"]{color:#175c3d}\n'
        '@media print{.review-status{display:none}}\n'
        '/* Both follows the existing section pairs')
    source = replace_once(source, 'function updateSaveState(){', '''function updateSaveState(){
  const badge = document.getElementById('review-status');
  const review = BandsheetReview.data.review;
  const dirtyReview = hasUnsavedChanges();
  badge.dataset.state = dirtyReview ? 'draft' : review.state;
  badge.textContent = dirtyReview ? 'Draft · unsaved changes' : review.label;''')
    source = replace_once(source, "    const next = {...data, sheetMeta, ...(revision ? {revision} : {draft: payload})};",
        """    const changed = revision !== base || (!base && hasUnsavedChanges());
    const review = changed ? {
      state: 'draft', revisionHash: sheetMeta.revisionHash || null, approvedAt: null,
      test: false, label: 'Draft · r' + sheetMeta.sheetRevision
    } : data.review;
    const next = {...data, sheetMeta, review, ...(revision ? {revision} : {draft: payload})};""")
    source = replace_once(source, "  if (payload.metadata.title) document.title = payload.metadata.title + ' · Bandsheet';",
        "  if (payload.metadata.title) document.title = payload.metadata.title + ' · rc.6 · r' + data.sheetMeta.sheetRevision;")
    source = replace_once(source,
        "var ar=document.getElementById('tb-artist').value;document.title=fn+' '+ar+' · bandsheet';updateSaveState()",
        "document.title=fn+' · rc.6 · r'+SHEET_META.sheetRevision;updateSaveState()")
    source = replace_once(source, "filenameSlug(payload.metadata.title) + '-review.html'",
        "filenameSlug(payload.metadata.title) + '-rc6-r' + sheetMeta.sheetRevision + '.html'")
    data['sheetMeta']['uiVersion'] = VERSION
    data['shellSha256'] = shell_hash(source.encode())
    data['review'] = review_projection(None, 'draft')
    prefix, _, suffix = split_slot(source.encode())
    return prefix + inline_data(data) + suffix


def trusted_decision(path, expected_sha, revision):
    raw = path.read_bytes()
    if sha256(raw).hexdigest() != expected_sha:
        raise ValueError('Decision differs from its externally supplied SHA-256')
    decision = contract.parse_json(raw.decode())
    if (not isinstance(decision, dict) or set(decision) != {
            'decision', 'scope', 'songId', 'revisionHash', 'approvedAt', 'approvedBy', 'evidenceRef'}
            or decision['decision'] != 'approved'
            or decision['songId'] != revision['songId']
            or decision['revisionHash'] != contract.revision_hash(revision)
            or not isinstance(decision['evidenceRef'], str) or not decision['evidenceRef'].strip()
            or not isinstance(decision['approvedAt'], str)
            or not re.fullmatch(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:Z|[+-]\d{2}:\d{2})', decision['approvedAt'])):
        raise ValueError('Expected an approval for this exact revision with a timestamp and evidence reference')
    datetime.fromisoformat(decision['approvedAt'].replace('Z', '+00:00'))
    is_test = revision['songId'].startswith('fixture-') and revision['provenance']['sourceType'] == 'synthetic-fixture'
    if is_test:
        valid_authority = decision['scope'] == 'synthetic-test' and decision['approvedBy'] == 'Test fixture'
    else:
        valid_authority = decision['scope'] == 'song-review' and decision['approvedBy'] == 'Ti'
    if not valid_authority:
        raise ValueError('Decision authority or scope is invalid for this revision')
    return decision


def review_data(template, revision, decision):
    data = BASE['revision_data'](revision)
    data['sheetMeta']['uiVersion'] = VERSION
    data['shellSha256'] = shell_hash(template)
    data['review'] = review_projection(revision, 'approved' if decision else 'pending', decision)
    return data


def verify(raw, template, decision_path, decision_sha):
    data = check_shell(raw, template)
    review = data['review']
    base = {key: value for key, value in data.items() if key != 'review'}
    if base['sheetMeta']['uiVersion'] != VERSION:
        raise ValueError('Unexpected template version')
    base['sheetMeta'] = {**base['sheetMeta'], 'uiVersion': BASE['VERSION']}
    BASE['validate_data'](base)
    revision = base.get('revision')
    state = review['state']
    if state not in ('draft', 'pending', 'approved') or (not revision and state != 'draft'):
        raise ValueError('Invalid review status')
    if (state == 'approved') != bool(decision_path):
        raise ValueError('Approved status requires the matching external decision')
    decision = trusted_decision(decision_path, decision_sha, revision) if decision_path else None
    expected = review_projection(revision, state, decision)
    if not revision:
        expected['label'] = f"Draft · r{base['sheetMeta']['sheetRevision']}"
    if review != expected:
        raise ValueError('Review status does not match the revision and decision')


def render_index(row):
    return f'''<!doctype html>
<html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Song review index</title>
<style>body{{margin:24px;color:#20324b;font:15px system-ui;background:#f7f9fc}}main{{max-width:46rem;margin:auto}}h1{{font-size:1.45rem}}article{{background:white;border:1px solid #dce3ed;padding:14px}}p{{margin:6px 0}}a{{color:#1557a0}}.status{{font-weight:600;overflow-wrap:anywhere}}</style>
<main><h1>Song review index</h1><article>
<a href="{escape(row['href'])}">{escape(row['title'])}</a>
<p class="status">{escape(row['review']['label'])}</p>
</article></main></html>
'''


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument('--check', action='store_true')
    action.add_argument('--output-dir', type=Path)
    action.add_argument('--verify', type=Path)
    parser.add_argument('--review-html', type=Path, help='An rc.5 or rc.6 Hysteria review export')
    parser.add_argument('--song-json', type=Path, help='A synthetic fixture')
    parser.add_argument('--decision', type=Path)
    parser.add_argument('--decision-sha256', help='SHA-256 from the trusted decision evidence')
    args = parser.parse_args()
    if bool(args.decision) != bool(args.decision_sha256):
        parser.error('--decision and --decision-sha256 must be supplied together')
    if args.output_dir:
        if bool(args.review_html) == bool(args.song_json):
            parser.error('Provide exactly one of --review-html and --song-json')
    elif args.review_html or args.song_json or (args.check and args.decision):
        parser.error('Input revisions require --output-dir')

    template = render_template()
    manifest = json.loads((FOLDER / 'manifest.json').read_text())
    if ((FOLDER / 'template.html').read_bytes() != template
            or sha256(template).hexdigest() != manifest['templateSha256']
            or shell_hash(template) != manifest['shellSha256']):
        raise ValueError('Locked rc.6 template differs')
    if args.check:
        print('Review template matches the pinned build')
        return
    if args.verify:
        verify(args.verify.read_bytes(), template, args.decision, args.decision_sha256)
        print('UI shell, revision and review status verified')
        return
    if args.review_html:
        raw = args.review_html.read_bytes()
        _, slot, _ = split_slot(raw)
        incoming = contract.parse_json(slot.decode('utf-8'))
        if incoming['sheetMeta']['uiVersion'] == VERSION:
            previous_approval = incoming['review']['state'] == 'approved'
            verify(raw, template, args.decision if previous_approval else None,
                   args.decision_sha256 if previous_approval else None)
            revision = incoming['revision']
        else:
            base_template = (BASE_FOLDER / 'template.html').read_bytes()
            revision = BASE['validate_data'](check_shell(raw, base_template))['revision']
        if (revision['songId'] != 'review-hysteria' or not revision['provenance'].get('sourceRef', '').endswith(
                '#sha256=3418e810eafe653418e5e00e92e8d23014d950b55bdf0960abb7174a0cdd1212')):
            raise ValueError('Only the Hysteria pilot is in scope')
    else:
        revision = contract.load_json(args.song_json)
        if not revision['songId'].startswith('fixture-') or revision['provenance']['sourceType'] != 'synthetic-fixture':
            raise ValueError('--song-json accepts synthetic fixtures only')
    decision = trusted_decision(args.decision, args.decision_sha256, revision) if args.decision else None
    data = review_data(template, revision, decision)
    prefix, _, suffix = split_slot(template)
    song = prefix + inline_data(data) + suffix
    verify(song, template, args.decision, args.decision_sha256)
    row = {'title': revision['metadata']['title'], 'href': 'song.html', 'review': data['review']}
    index = render_index(row)
    args.output_dir.mkdir()
    (args.output_dir / 'song.html').write_bytes(song)
    (args.output_dir / 'catalog.json').write_text(json.dumps({'songs': [row]}, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    (args.output_dir / 'index.html').write_text(index, encoding='utf-8')


if __name__ == '__main__':
    main()
