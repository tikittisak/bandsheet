#!/usr/bin/env python3
"""Experimental lossless transfer to a NEW scratch artifact, never canonical.

No legacy importer dependencies, normalization, schema repair or inferred data.
"""
import argparse
import hashlib
import html
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
VERSION = 'trial-0.1'
FIELDS = ('tb-filename','tb-artist','meta-key','meta-bpm','meta-time','meta-vocalist')
BLOCKS = {'SECTIONS':'DATA','FOOTER':'FOOTER','SETTINGS':'SETTINGS','SHEET_META':'SHEET META'}
TEMPLATE = ROOT/'_archive/prototypes/luminous-v7.0.0-alpha.2-blank.html'
TEMPLATE_HASH = '3fe27ae27f4dcde6347e9016d0d569f0060c95436bad3259dccb3e60eedb31fa'


def sha(data):
    return hashlib.sha256(data).hexdigest()


def unique_object(pairs):
    out = {}
    for key, value in pairs:
        if key in out:
            raise ValueError('duplicate JSON key: '+key)
        out[key] = value
    return out


class Metadata(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.values = {}

    def handle_starttag(self, tag, attrs):
        data = dict(attrs)
        key = data.get('id')
        if tag == 'input' and key in FIELDS:
            if key in self.values or 'value' not in data:
                raise ValueError('duplicate or valueless metadata input: '+key)
            self.values[key] = data['value']


def span(doc, name):
    marker = '// ── END '+BLOCKS[name]+' ──'
    declaration = 'var '+name+' = '
    markers = list(re.finditer(r'^'+re.escape(marker)+r'\s*$',doc,re.M))
    declarations = list(re.finditer(r'^'+re.escape(declaration),doc,re.M))
    if len(markers) != 1 or len(declarations) != 1:
        raise ValueError('missing/ambiguous block: '+name)
    end = markers[0].start()
    start = declarations[0].end()
    if start >= end:
        raise ValueError('invalid block order: '+name)
    raw = doc[start:end].strip()
    if not raw.endswith(';'):
        raise ValueError('missing block terminator: '+name)
    return start, end, raw[:-1].strip()


def snapshot(doc):
    parser = Metadata(); parser.feed(doc); parser.close()
    if set(parser.values) != set(FIELDS):
        raise ValueError('missing metadata')
    result = {'metadata':parser.values}
    for name in BLOCKS:
        raw = span(doc,name)[2]
        result[name] = json.loads(raw, object_pairs_hook=unique_object,
                                 parse_constant=lambda x: (_ for _ in ()).throw(ValueError(x)))
    return result


def canonical(data):
    return json.dumps(data,ensure_ascii=False,sort_keys=True,separators=(',',':'))


def assert_equal(before, after):
    if canonical(before) != canonical(after):
        different = [k for k in before if canonical(before[k]) != canonical(after.get(k))]
        raise ValueError('STOP: semantic divergence: '+', '.join(different))


def render(source, template):
    expected = snapshot(source)
    snapshot(template)  # Fail closed on missing/duplicate template anchors.
    output = template
    for name in BLOCKS:
        raw = span(source,name)[2]
        start,end,_ = span(output,name)
        # Preserve source JSON values/unknown fields, while escaping HTML parser terminators.
        output = output[:start]+raw.replace('<','\\u003c')+';\n'+output[end:]
    for key,value in expected['metadata'].items():
        pattern = r'(id="'+re.escape(key)+r'"[^>]*value=")[^"]*(")'
        output,count = re.subn(pattern,lambda m:m[1]+html.escape(value,quote=True)+m[2],output)
        if count != 1:
            raise ValueError('ambiguous metadata replacement: '+key)
    output,count = re.subn(r'<title>[^<]*</title>',lambda _: '<title>'+html.escape(expected['metadata']['tb-filename'])+' · Luminous trial</title>',output,count=1)
    if count != 1:
        raise ValueError('missing title')
    assert_equal(expected,snapshot(output))
    return output


def create_trial(source, expected_hash, band):
    source = source.resolve()
    if source.parent != ROOT/'songs' or source.suffix != '.html':
        raise ValueError('source must be a canonical songs/*.html file')
    members = json.loads((ROOT/'bands'/f'{band}.json').read_text())['songs']
    if source.name not in members:
        raise ValueError('source not in selected band')
    original = source.read_bytes()
    if sha(original) != expected_hash:
        raise ValueError('source hash changed; reselect source before proceeding')
    template = TEMPLATE.read_bytes()
    if sha(template) != TEMPLATE_HASH:
        raise ValueError('template hash changed; independent review required')
    output = render(original.decode(),template.decode())
    if source.read_bytes() != original:
        raise ValueError('source changed during transfer')
    folder = ROOT/'_work/transfer-trials'; folder.mkdir(parents=True,exist_ok=True)
    trial = Path(tempfile.mkdtemp(prefix=source.stem+'-',dir=folder))
    for name,body in [('source.html',original),('trial.html',output.encode())]:
        with (trial/name).open('xb') as f:f.write(body)
    data=snapshot(output)
    report={'toolVersion':VERSION,'toolSha256':sha(Path(__file__).read_bytes()),
            'source':str(source.relative_to(ROOT)),'sourceSha256':sha(original),
            'sourceGitHead':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
            'template':str(TEMPLATE.relative_to(ROOT)),'templateSha256':sha(template),
            'output':'trial.html','outputSha256':sha(output.encode()),'embeddedEquality':True,
            'payloadSha256':sha(canonical(data).encode()),'runtimeVerification':'pending',
            'musicalApproval':False,'canonicalPromotion':False,
            'sections':len(data['SECTIONS']),'bars':sum(len(s.get('bars',[])) for s in data['SECTIONS'])}
    (trial/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    (trial/'expected.json').write_text(canonical(data)+'\n')
    return trial


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source',type=Path)
    parser.add_argument('--expected-sha256',required=True)
    parser.add_argument('--band',choices=['tmj'],required=True)
    args=parser.parse_args()
    try:print(create_trial(args.source,args.expected_sha256,args.band))
    except (ValueError,OSError) as exc:parser.exit(1,str(exc)+'\n')
