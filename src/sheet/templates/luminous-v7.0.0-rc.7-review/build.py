#!/usr/bin/env python3
"""Build a song review bundle with revision and approval times in ICT."""
import argparse
from datetime import date, datetime, timedelta, timezone
from hashlib import sha256
from html import escape
import json
from pathlib import Path
import re
import runpy

FOLDER = Path(__file__).resolve().parent
BASE_FOLDER = FOLDER.with_name('luminous-v7.0.0-rc.6-review')
BASE = runpy.run_path(str(BASE_FOLDER / 'build.py'))
RC5 = BASE['BASE']
BASE_SHA = '9570ba1b4b13a16939f7dc8b0ba0c4a5898271b79bbc0c6d2deec4ec87735037'
VERSION = '7.0.0-rc.7-review'
ICT = timezone(timedelta(hours=7))
MONTHS = 'Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec'.split()
contract = BASE['contract']
split_slot = BASE['split_slot']
inline_data = BASE['inline_data']
shell_hash = BASE['shell_hash']
check_shell = BASE['check_shell']
replace_once = BASE['replace_once']


def display_time(value, date_only=False):
    when = (date.fromisoformat(value) if date_only else
            datetime.fromisoformat(value.replace('Z', '+00:00')).astimezone(ICT))
    day = f'{when.day} {MONTHS[when.month - 1]} {when.year}'
    return day + (' (time unavailable)' if date_only else f', {when:%H:%M} ICT')


def review_projection(revision, state, decision=None, *, blank_day=None, blank_time=None, number=1):
    review = BASE['review_projection'](revision, state, decision)
    if review['approvedAt']:
        review['label'] = review['label'].removesuffix(' · ' + review['approvedAt'])
    if not revision:
        review['label'] = f'Draft · r{number}'
    provenance = revision['provenance'] if revision else {}
    edited_at = provenance.get('editedAt') if revision else blank_time
    edited_on = provenance.get('capturedOn') if revision else blank_day
    review.update(editedAt=edited_at, editedOn=None if edited_at else edited_on)
    return review


def render_template():
    raw = (BASE_FOLDER / 'template.html').read_bytes()
    if sha256(raw).hexdigest() != BASE_SHA or BASE['render_template']() != raw:
        raise ValueError('Pinned rc.6 template differs')
    prefix, slot, suffix = split_slot(raw)
    data = contract.parse_json(slot.decode())
    source = (prefix + suffix).decode().replace(BASE['VERSION'], VERSION)
    source = source.replace(' · rc.6 · r', ' · rc.7 · r').replace("'-rc6-r'", "'-rc7-r'")
    source = replace_once(source,
        '<div id="review-status" role="status" class="review-status">Draft</div>',
        '<div class="review-timeline"><div id="review-status" role="status" class="review-status">Draft</div>'
        '<div id="review-edited"></div><div id="review-approved"></div></div>')
    source = replace_once(source, '.review-status{padding:6px 12px;',
        '.review-timeline{padding:6px 12px;color:#42546e;font:12px/1.5 system-ui;overflow-wrap:anywhere}\n'
        '.review-timeline div:empty{display:none}\n'
        '.review-status{')
    source = replace_once(source, '@media print{.review-status{display:none}}',
        '@media print{.review-timeline{display:none}}')
    timeline = (FOLDER / 'timeline.js').read_text(encoding='utf-8')
    if '</script' in timeline.lower():
        raise ValueError('Unexpected timeline script boundary')
    source = replace_once(source, 'let lastLocalExport;', timeline + '\nlet lastLocalExport;')
    source = replace_once(source, "  badge.textContent = dirtyReview ? 'Draft · unsaved changes' : review.label;",
        """  badge.textContent = dirtyReview ? 'Draft · unsaved changes' : review.label;
  trackReviewEdit(currentSheetSignature());
  updateReviewTimeline(review, dirtyReview);""")
    source = replace_once(source, '  const signature = currentSheetSignature();',
        '  const signature = currentSheetSignature();\n  const editedAt = trackReviewEdit(signature);')
    source = replace_once(source, '            capturedOn: new Date().toISOString().slice(0, 10),',
        '            capturedOn: new Date().toISOString().slice(0, 10),\n            editedAt,')
    source = replace_once(source, "      test: false, label: 'Draft · r' + sheetMeta.sheetRevision",
        "      test: false, label: 'Draft · r' + sheetMeta.sheetRevision, editedAt, editedOn: null")
    data['sheetMeta']['uiVersion'] = VERSION
    data['shellSha256'] = shell_hash(source.encode())
    data['review'] = review_projection(None, 'draft')
    prefix, _, suffix = split_slot(source.encode())
    return prefix + inline_data(data) + suffix


def verify(raw, template, decision_path=None, decision_sha=None):
    data = check_shell(raw, template)
    review = data['review']
    prior = {key: value for key, value in data.items() if key != 'review'}
    if prior['sheetMeta']['uiVersion'] != VERSION:
        raise ValueError('Unexpected template version')
    meta = prior['sheetMeta']
    prior['sheetMeta'] = {**meta, 'uiVersion': RC5['VERSION']}
    RC5['validate_data'](prior)
    revision = prior.get('revision')
    state = review['state']
    if state not in ('draft', 'pending', 'approved') or (not revision and state != 'draft'):
        raise ValueError('Invalid review status')
    if (state == 'approved') != bool(decision_path):
        raise ValueError('Approved status requires the matching external decision')
    decision = BASE['trusted_decision'](decision_path, decision_sha, revision) if decision_path else None
    blank_time = None
    if not revision and meta['contentUpdated']:
        blank_time = review['editedAt']
        if blank_time is not None:
            if not isinstance(blank_time, str) or not re.fullmatch(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z', blank_time):
                raise ValueError('Invalid local draft edit time')
            display_time(blank_time)
    expected = review_projection(revision, state, decision, blank_day=meta['contentUpdated'] or None,
                                 blank_time=blank_time, number=meta['sheetRevision'])
    if review != expected:
        raise ValueError('Review status or edit time does not match its revision')
    return data


def read_review(path, template, decision, decision_sha):
    raw = path.read_bytes()
    incoming = contract.parse_json(split_slot(raw)[1].decode('utf-8'))
    version = incoming['sheetMeta']['uiVersion']
    approved = incoming.get('review', {}).get('state') == 'approved'
    args = (decision, decision_sha) if approved else (None, None)
    if version == VERSION:
        verify(raw, template, *args)
    elif version == BASE['VERSION']:
        BASE['verify'](raw, (BASE_FOLDER / 'template.html').read_bytes(), *args)
    elif version == RC5['VERSION']:
        RC5['validate_data'](check_shell(raw, (BASE['BASE_FOLDER'] / 'template.html').read_bytes()))
    else:
        raise ValueError(f'Unsupported review template version: {version}')
    revision = incoming.get('revision')
    if (not revision or revision['songId'] != 'review-hysteria' or not revision['provenance'].get('sourceRef', '').endswith(
            '#sha256=3418e810eafe653418e5e00e92e8d23014d950b55bdf0960abb7174a0cdd1212')):
        raise ValueError('Only the Hysteria pilot is in scope')
    return revision


def render_index(row):
    review = row['review']
    lines = []
    if review['editedAt'] or review['editedOn']:
        lines.append('Last edited: ' + display_time(review['editedAt'] or review['editedOn'], not review['editedAt']))
    if review['approvedAt']:
        lines.append('Approved on: ' + display_time(review['approvedAt']))
    source = BASE['render_index'](row)
    return replace_once(source, '</article>', ''.join('<p>' + escape(line) + '</p>\n' for line in lines) + '</article>')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument('--check', action='store_true')
    action.add_argument('--output-dir', type=Path)
    action.add_argument('--verify', type=Path)
    parser.add_argument('--review-html', type=Path)
    parser.add_argument('--song-json', type=Path, help='A synthetic fixture')
    parser.add_argument('--decision', type=Path)
    parser.add_argument('--decision-sha256')
    args = parser.parse_args()
    if bool(args.decision) != bool(args.decision_sha256):
        parser.error('--decision and --decision-sha256 must be supplied together')
    if args.output_dir and bool(args.review_html) == bool(args.song_json):
        parser.error('Provide exactly one of --review-html and --song-json')
    if not args.output_dir and (args.review_html or args.song_json or (args.check and args.decision)):
        parser.error('Input revisions require --output-dir')
    template = render_template()
    manifest = json.loads((FOLDER / 'manifest.json').read_text(encoding='utf-8'))
    if ((FOLDER / 'template.html').read_bytes() != template
            or sha256(template).hexdigest() != manifest['templateSha256']
            or shell_hash(template) != manifest['shellSha256']):
        raise ValueError('Locked rc.7 template differs')
    if args.check:
        print('Review template matches the pinned build')
        return
    if args.verify:
        verify(args.verify.read_bytes(), template, args.decision, args.decision_sha256)
        print('UI shell, revision and review timestamps verified')
        return
    if args.review_html:
        revision = read_review(args.review_html, template, args.decision, args.decision_sha256)
    else:
        revision = contract.load_json(args.song_json)
        if not revision['songId'].startswith('fixture-') or revision['provenance']['sourceType'] != 'synthetic-fixture':
            raise ValueError('--song-json accepts synthetic fixtures only')
    decision = BASE['trusted_decision'](args.decision, args.decision_sha256, revision) if args.decision else None
    data = RC5['revision_data'](revision)
    data['sheetMeta']['uiVersion'] = VERSION
    data['shellSha256'] = shell_hash(template)
    data['review'] = review_projection(revision, 'approved' if decision else 'pending', decision)
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
