#!/usr/bin/env python3
"""Build the review template with B/I/U and render local review HTML from JSON."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

FOLDER = Path(__file__).resolve().parent
ROOT = FOLDER.parents[3]
VERSION = '7.0.0-rc.4-review'
BASE = ROOT / 'src/sheet/templates/luminous-v7.0.0-rc.3-review/template.html'
BASE_SHA256 = 'ece138080458c0807b225c1be5077e7c3eba45bf9af952177bbcce920fad6d0d'


def sha256(value):
    return hashlib.sha256(value).hexdigest()


def render():
    source = BASE.read_bytes()
    if sha256(source) != BASE_SHA256:
        raise ValueError('Pinned rc.3 template hash mismatch')
    document = source.decode('utf-8')
    if document.count('7.0.0-rc.3-review') != 3:
        raise ValueError('Unexpected version anchors')
    document = document.replace('7.0.0-rc.3-review', VERSION)
    old_editor = (BASE.parent / 'editor.js').read_text(encoding='utf-8')
    editor = (FOLDER / 'editor.js').read_text(encoding='utf-8')
    if document.count(old_editor) != 1 or '</script' in editor.lower():
        raise ValueError('Invalid editor script boundary')
    document = document.replace(old_editor, editor, 1)
    style = '.lyric-italic { font-style: italic; }'
    if document.count(style) != 1:
        raise ValueError('Unexpected formatting style anchor')
    document = document.replace(style, style + '\n.lyric-underline { text-decoration: underline; }', 1)
    # Each retired function has only its declaration or a caller in this same
    # retired block. Fail if the pinned source gains a new reference.
    for name, expected in [('injectData', 1), ('cleanRuntimeHtml', 2), ('downloadTemplate', 1), ('auditEscape', 1)]:
        if document.count(name + '(') != expected:
            raise ValueError(f'Unexpected call sites for {name}')
    for first, following in [('injectData', 'filenameSlug'), ('downloadTemplate', 'saveToFile')]:
        start, end = 'function ' + first + '(', 'function ' + following + '('
        if document.count(start) != 1 or document.count(end) != 1:
            raise ValueError(f'Ambiguous removal boundary for {first}')
        document = document[:document.index(start)] + document[document.index(end):]
    return document.encode('utf-8')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument('--check', action='store_true')
    action.add_argument('--output', type=Path)
    parser.add_argument('--song-json', type=Path, help='Render a review copy from a validated JSON revision.')
    args = parser.parse_args()
    if args.song_json and not args.output:
        parser.error('--song-json requires --output')
    generated = render()
    manifest = json.loads((FOLDER / 'manifest.json').read_text(encoding='utf-8'))
    if sha256(generated) != manifest['templateSha256']:
        raise ValueError('Review template hash mismatch')
    if args.check:
        if (FOLDER / 'template.html').read_bytes() != generated:
            raise ValueError('Local template differs from the pinned build')
        print('Review template matches the pinned build')
        return
    if args.song_json:
        sys.path.insert(0, str(ROOT / 'tools'))
        import song_data_contract as contract
        generated = contract.render_song_html(
            generated.decode(), contract.load_json(args.song_json), VERSION, local_review=True,
        ).encode()
    with args.output.open('xb') as output:
        output.write(generated)


if __name__ == '__main__':
    main()
