#!/usr/bin/env python3
"""Build and verify review HTML with exactly one replaceable data slot."""
import argparse
from hashlib import sha256
import json
from pathlib import Path
import re
import sys

FOLDER = Path(__file__).resolve().parent
ROOT = FOLDER.parents[3]
sys.path.insert(0, str(ROOT / 'tools'))
import song_data_contract as contract
import transfer_song_trial as transfer

VERSION = '7.0.0-rc.5-review'
FORMAT = 'bandsheet-review-html-1'
BASE = ROOT / 'src/sheet/templates/luminous-v7.0.0-rc.4-review/template.html'
BASE_SHA256 = '5de6e8a31c78701fc86a91a1c47c579a26b0eef33d8e7420be272d977498c226'
SLOT = b'<script id="bandsheet-review-data" type="application/json">'


def split_slot(document):
    if document.count(SLOT) != 1:
        raise ValueError('Expected exactly one review data slot')
    prefix, tail = document.split(SLOT, 1)
    data, end, suffix = tail.partition(b'</script>')
    if not end or b'<' in data:
        raise ValueError('Invalid review data boundary')
    return prefix + SLOT, data, end + suffix


def inline_data(data):
    return contract.document_json(data).replace('<', r'\u003c').replace(
        '>', r'\u003e').replace('&', r'\u0026').encode('utf-8')


def shell_hash(document):
    prefix, _, suffix = split_slot(document)
    return sha256(prefix + suffix).hexdigest()


def check_shell(document, template):
    actual = split_slot(document)
    expected = split_slot(template)
    for side, index in [('before', 0), ('after', 2)]:
        got, wanted = actual[index], expected[index]
        if got != wanted:
            mismatch = next((i for i, (a, b) in enumerate(zip(got, wanted)) if a != b), min(len(got), len(wanted)))
            raise ValueError(f'UI differs {side} data slot at byte {mismatch}: '
                             f'expected {wanted[mismatch:mismatch+35]!r}; got {got[mismatch:mismatch+35]!r}')
    data = contract.parse_json(actual[1].decode('utf-8'))
    if not isinstance(data, dict) or data.get('shellSha256') != shell_hash(template):
        raise ValueError('Review data carries a different UI shell hash')
    return data


def revision_data(revision):
    contract.validate_song(revision)
    provenance = revision['provenance']
    return {'format': FORMAT, 'revision': revision, 'sheetMeta': {
        'templateVersion': 'v6.19',
        'uiVersion': VERSION,
        'dataSchemaVersion': revision['schemaVersion'],
        'songId': revision['songId'],
        'sheetRevision': revision['contentRevision'],
        'contentRevision': revision['contentRevision'],
        'contentUpdated': provenance['capturedOn'],
        'contentSource': provenance['sourceType'],
        'contentHash': contract.content_hash(revision),
        'revisionHash': contract.revision_hash(revision),
        'parentRevisionHash': provenance['parentRevisionHash'],
    }}


def validate_data(data):
    if (not isinstance(data, dict) or data.get('format') != FORMAT
            or not re.fullmatch(r'[0-9a-f]{64}', str(data.get('shellSha256', '')))):
        raise ValueError('Unsupported review data format or UI shell hash')
    envelope = data
    data = {key: value for key, value in envelope.items() if key != 'shellSha256'}
    if set(data) == {'format', 'revision', 'sheetMeta'}:
        if contract.canonical(data) != contract.canonical(revision_data(data['revision'])):
            raise ValueError('Revision metadata or hash mismatch')
    elif set(data) == {'format', 'draft', 'sheetMeta'}:
        draft, meta = data['draft'], data['sheetMeta']
        if (not isinstance(draft, dict) or set(draft) != {'metadata', 'sections', 'footer', 'settings', 'extensions'}
                or not isinstance(draft['metadata'], dict)):
            raise ValueError('Invalid local draft payload')
        if (not isinstance(meta, dict) or set(meta) != {
                'templateVersion', 'uiVersion', 'sheetRevision', 'contentUpdated', 'contentSource'}
                or meta['templateVersion'] != 'v6.19' or meta['uiVersion'] != VERSION
                or type(meta['sheetRevision']) is not int or meta['sheetRevision'] < 1
                or not isinstance(meta['contentUpdated'], str)
                or meta['contentSource'] not in ('blank-baseline', 'local-html-draft')):
            raise ValueError('Invalid local draft metadata')
        # Check a blank title using the same payload schema without filling it in.
        metadata = dict(draft['metadata'])
        if isinstance(metadata.get('title'), str) and not metadata['title'].strip():
            metadata['title'] = 'Blank template'
        contract.validate_song({
            **draft, 'metadata': metadata, 'schemaVersion': 1, 'songId': 'blank-review',
            'slug': 'blank-review', 'contentRevision': meta['sheetRevision'],
            'provenance': {'sourceType': meta['contentSource'], 'capturedOn': meta['contentUpdated'] or '2026-11-07',
                           'parentRevisionHash': None},
        })
    else:
        raise ValueError('Expected one draft or revision payload')
    return envelope


def render_template():
    base = BASE.read_bytes()
    if sha256(base).hexdigest() != BASE_SHA256:
        raise ValueError('Pinned rc.4 template hash mismatch')
    original = base.decode('utf-8')
    blank = transfer.snapshot(original)
    data = {'format': FORMAT, 'sheetMeta': {**blank['SHEET_META'], 'uiVersion': VERSION}, 'draft': {
        'metadata': {key: blank['metadata'][id_] for key, id_ in contract.INPUT_IDS.items()},
        'sections': blank['SECTIONS'], 'footer': blank['FOOTER'], 'settings': blank['SETTINGS'], 'extensions': {},
    }}
    document = original
    old_editor = (BASE.parent / 'editor.js').read_text(encoding='utf-8')
    editor = (FOLDER / 'editor.js').read_text(encoding='utf-8')
    bootstrap = (FOLDER / 'bootstrap.js').read_text(encoding='utf-8')
    if document.count(old_editor) != 1 or '</script' in (editor + bootstrap).lower():
        raise ValueError('Invalid editor or bootstrap boundary')
    document = document.replace(old_editor, editor, 1)
    for name, access in [('SECTIONS', 'payload.sections'), ('FOOTER', 'payload.footer'),
                         ('SETTINGS', 'payload.settings'), ('SHEET_META', 'data.sheetMeta')]:
        start, end, _ = transfer.span(document, name)
        document = document[:start] + f'structuredClone(BandsheetReview.{access});\n' + document[end:]
    if document.count('7.0.0-rc.4-review') != 2:
        raise ValueError('Unexpected version anchors')
    document = document.replace('7.0.0-rc.4-review', VERSION)
    document, script_count = re.subn(r'^<script( id="[^"]+")?>$', lambda m:
        '<script' + (m[1] or '') + ' type="application/x-bandsheet-js">', document, flags=re.MULTILINE)
    if script_count != 4 or document.count('</body>') != 1:
        raise ValueError('Unexpected template startup scripts')
    # Match HTML serialization at the bootstrap boundary: the browser has not
    # parsed trailing whitespace yet, and writes attributes on one line.
    button = 'id="bar-number-btn" type="button"\n      onclick='
    if document.count(button) != 1 or not document.endswith('</body></html>\n'):
        raise ValueError('Unexpected HTML serialization anchors')
    document = document.replace(button, 'id="bar-number-btn" type="button" onclick=', 1)
    document = document.replace('<!DOCTYPE html>', '<!doctype html>', 1).removesuffix('\n')
    tail = SLOT + inline_data(data) + b'</script>\n<script>\n' + bootstrap.encode() + b'</script></body>'
    html = document.encode('utf-8').replace(b'</body>', tail, 1)
    prefix, _, suffix = split_slot(html)
    data['shellSha256'] = shell_hash(html)
    return prefix + inline_data(validate_data(data)) + suffix


def check_template_pin(template):
    manifest = json.loads((FOLDER / 'manifest.json').read_text(encoding='utf-8'))
    if (sha256(template).hexdigest() != manifest['templateSha256'] or
            shell_hash(template) != manifest['shellSha256']):
        raise ValueError('Locked review template or UI shell differs from the build')
    return manifest['shellSha256']


def render_song(template, revision):
    pin = check_template_pin(template)
    prefix, _, suffix = split_slot(template)
    data = {**revision_data(revision), 'shellSha256': pin}
    output = prefix + inline_data(data) + suffix
    if contract.canonical(check_shell(output, template)) != contract.canonical(data):
        raise ValueError('Review revision changed during render')
    return output


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument('--check', action='store_true')
    action.add_argument('--output', type=Path)
    action.add_argument('--verify', type=Path)
    parser.add_argument('--song-json', type=Path)
    args = parser.parse_args()
    if args.song_json and not args.output:
        parser.error('--song-json requires --output')

    template = render_template()
    check_template_pin(template)
    if (FOLDER / 'template.html').read_bytes() != template:
        raise ValueError('Local template differs from the pinned build')
    if args.check:
        print('Review template and UI shell match the pinned build')
    elif args.verify:
        validate_data(check_shell(args.verify.read_bytes(), template))
        print('UI shell and review data verified')
    else:
        output = render_song(template, contract.load_json(args.song_json)) if args.song_json else template
        with args.output.open('xb') as file:
            file.write(output)


if __name__ == '__main__':
    main()
