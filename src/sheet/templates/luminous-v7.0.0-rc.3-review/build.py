#!/usr/bin/env python3
"""Build the local review template and render a review HTML copy from a JSON revision."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

FOLDER = Path(__file__).resolve().parent
ROOT = FOLDER.parents[3]
VERSION = '7.0.0-rc.3-review'
BASE = ROOT / 'src/sheet/templates/luminous-v7.0.0-rc.2-review/template.html'
BASE_SHA256 = '796bae1359ba824009976a3915c903709567abdf12ad940b9d56bd277cdf02ff'
PROTOCOL = ROOT / 'src/sheet/revision-client.js'
PROTOCOL_SHA256 = 'b8450f31b87dcc00f628861ca235835039449780d08f5ec5c058a3f3d06effb9'


def sha256(value):
    return hashlib.sha256(value).hexdigest()


def pinned(path, digest):
    data = path.read_bytes()
    if sha256(data) != digest:
        raise ValueError(f'Unexpected input hash: {path.name}')
    return data.decode('utf-8')


def replace_once(document, original, replacement):
    if document.count(original) != 1:
        raise ValueError(f'Template anchor missing or ambiguous: {original[:80]!r}')
    return document.replace(original, replacement, 1)


def render():
    document = pinned(BASE, BASE_SHA256)
    if document.count('7.0.0-rc.2-review') != 3:
        raise ValueError('Unexpected version anchors')
    document = document.replace('7.0.0-rc.2-review', VERSION)
    codec = pinned(PROTOCOL, PROTOCOL_SHA256)
    boundary = '  if(typeof document===\'undefined\')return;'
    if codec.count(boundary) != 1:
        raise ValueError('Revision protocol boundary changed')
    codec = codec.split(boundary, 1)[0] + '})();\n'
    editor = (FOLDER / 'editor.js').read_text(encoding='utf-8')
    if '</script' in (codec + editor).lower():
        raise ValueError('Unsafe closing tag in editor source')
    document = replace_once(document, '<script>\nvar PRESETS=', (
        '<script id="bandsheet-local-html-export">\n' + codec + editor +
        '</script>\n<script id="bandsheet-sheet-data">\nvar PRESETS='
    ))
    document = replace_once(document, '</style>\n</head>', '''body.edit-mode .lyric-format-toolbar {
  display: flex !important;
  gap: 4px;
  flex-wrap: wrap;
  margin: 0 0 4px;
}
.lyric-format-toolbar .rte-btn { min-height: 28px; }
.lyric-bold { font-weight: 700; }
.lyric-italic { font-style: italic; }
.rte-editor b, .rte-editor strong { font-weight: 700; }
</style>
</head>''')
    document = replace_once(document, '''        ed.oninput=ed.onblur=(function(s,c){return function(){SECTIONS[s].cols[c]=this.innerHTML}})(si,dataCi);''',
        '''        ed.oninput=(function(s,c){return function(){SECTIONS[s].cols[c]=this.innerHTML;updateSaveState()}})(si,dataCi);
        if(EDIT_MODE)colWrap.appendChild(makeLyricFormatToolbar(ed));''')
    document = replace_once(document, '<button class="tb-btn primary" onclick="saveToFile()" title="Save current sheet as HTML">',
        '<button class="tb-btn primary" id="local-save-html-btn" onclick="saveToFile()" title="Download a local HTML draft">')
    document = replace_once(document, "el.textContent=dirty?'unsaved changes':'loaded / export requested';",
        "el.textContent=localExportStatus()||(dirty?'unsaved changes':'local review');")
    begin, end = 'function saveToFile(){', '\nfunction updateTitle(){'
    if document.count(begin) != 1 or document.count(end) != 1:
        raise ValueError('Save boundaries changed')
    document = document[:document.index(begin)] + 'function saveToFile(){return exportLocalReviewHtml()}\n' + document[document.index(end):]
    return document.encode('utf-8')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument('--check', action='store_true')
    action.add_argument('--output', type=Path)
    parser.add_argument('--song-json', type=Path, help='Render a local review copy from a validated song revision.')
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
        revision = contract.load_json(args.song_json)
        generated = contract.render_song_html(generated.decode(), revision, VERSION, local_review=True).encode()
    with args.output.open('xb') as output:
        output.write(generated)


if __name__ == '__main__':
    main()
