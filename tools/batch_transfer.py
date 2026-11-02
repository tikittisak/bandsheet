#!/usr/bin/env python3
"""Plan and verify lossless review copies. Never promote canonical songs."""
import argparse
import hashlib
import html
import json
from pathlib import Path
import subprocess
import tempfile

import transfer_song_trial as transfer

ROOT=Path(__file__).resolve().parents[1]
TEMPLATE=Path('_archive/prototypes/luminous-v7.0.0-alpha.2-blank.html')
VERSION='batch-review-0.2'

def sha(data):return hashlib.sha256(data).hexdigest()
def dump(data):return json.dumps(data,ensure_ascii=False,indent=2)+'\n'
def inside(rel):
    p=(ROOT/rel).resolve()
    if not p.is_relative_to(ROOT):raise ValueError('path outside project')
    return p
def git(*args):return subprocess.check_output(['git',*args],cwd=ROOT,text=True).strip()
def template_clean(path):return not git('status','--porcelain','--',str(path))

def make_plan(band='all',template_path=TEMPLATE):
    members={}
    for path in sorted((ROOT/'bands').glob('*.json')):
        for name in json.loads(path.read_text())['songs']:
            members.setdefault(name,[]).append(path.stem)
    files=sorted((ROOT/'songs').glob('*.html'))
    if band!='all':files=[p for p in files if band in members.get(p.name,[])]
    if not files:raise ValueError('scope has no songs')
    selected=inside(template_path)
    template=selected.read_bytes();transfer.snapshot(template.decode())
    rows=[]
    for path in files:
        raw=path.read_bytes()
        row={'source':str(path.relative_to(ROOT)),'sourceSha256':sha(raw),
             'bands':members.get(path.name,[]),'manualReview':'pending','issues':[]}
        try:
            payload=transfer.snapshot(raw.decode())
            # Exercise candidate construction before promising a transferable row.
            candidate=transfer.render(raw.decode(),template.decode())
            transfer.assert_equal(payload,transfer.snapshot(candidate))
            bars=sum(len(s.get('bars',[])) for s in payload['SECTIONS'])
            lyrics=sum(s.get('type')=='note' for s in payload['SECTIONS'])
            row.update(title=payload['metadata']['tb-filename'],bars=bars,lyricBlocks=lyrics,
                       payloadSha256=sha(transfer.canonical(payload).encode()),preflight='pass')
            if bars<=4:row['issues'].append('blank/incomplete arrangement; preserve as-is')
            if not lyrics:row['issues'].append('no lyric blocks; manual intent check required')
            if payload['SHEET_META'].get('contentSource')=='migration-baseline':
                row['issues'].append('historical provenance gap; disk copy is not certified latest browser revision')
        except (ValueError,TypeError,KeyError) as exc:
            row.update(preflight='blocked',error=str(exc))
        rows.append(row)
    return {'version':VERSION,'gitHead':git('rev-parse','HEAD'),'scope':band,
            'toolSha256':sha(Path(__file__).read_bytes()),
            'transferLibrarySha256':sha(Path(transfer.__file__).read_bytes()),
            'template':str(selected.relative_to(ROOT)),'templateSha256':sha(template),
            'templateCleanAtPlanning':template_clean(selected.relative_to(ROOT)),
            'sourceSelection':'canonical disk snapshots only; browser/export recency not certified',
            'promotionAllowed':False,'songs':rows}

def preflight(plan):
    if plan.get('version')!=VERSION:raise ValueError('unsupported plan')
    if plan['toolSha256']!=sha(Path(__file__).read_bytes()) or plan['transferLibrarySha256']!=sha(Path(transfer.__file__).read_bytes()):
        raise ValueError('transfer code changed; make a new reviewed plan')
    path=inside(plan['template']);template=path.read_bytes()
    if sha(template)!=plan['templateSha256']:raise ValueError('template changed; stop and replan')
    if not template_clean(Path(plan['template'])):raise ValueError('UI template has uncommitted changes; freeze UI revision first')
    prepared=[];seen=set()
    for row in plan['songs']:
        source=inside(row['source'])
        if source.parent!=ROOT/'songs' or source.suffix!='.html' or source.name in seen:
            raise ValueError('invalid or duplicate source target')
        seen.add(source.name)
        raw=source.read_bytes()
        if sha(raw)!=row['sourceSha256']:raise ValueError('source changed: '+row['source'])
        if row.get('preflight')!='pass':raise ValueError('blocked plan row: '+row['source'])
        payload=transfer.snapshot(raw.decode())
        if sha(transfer.canonical(payload).encode())!=row['payloadSha256']:raise ValueError('source payload mismatch')
        candidate=transfer.render(raw.decode(),template.decode())
        transfer.assert_equal(payload,transfer.snapshot(candidate))
        prepared.append((row,raw,candidate))
    # Detect changes during the whole preflight, before creating output folders.
    if sha(path.read_bytes())!=plan['templateSha256']:raise ValueError('template changed during preflight')
    for row,_,_ in prepared:
        if sha(inside(row['source']).read_bytes())!=row['sourceSha256']:raise ValueError('source changed during preflight')
    return prepared

def execute(plan_path,expected_plan_sha):
    raw=plan_path.read_bytes()
    if sha(raw)!=expected_plan_sha:raise ValueError('plan hash mismatch')
    plan=json.loads(raw);prepared=preflight(plan)
    parent=ROOT/'_work/batch-transfer';parent.mkdir(parents=True,exist_ok=True)
    run=Path(tempfile.mkdtemp(prefix='review-',dir=parent))
    (run/'sources').mkdir();(run/'songs').mkdir()
    records=[];table=[]
    for row,original,candidate in prepared:
        name=Path(row['source']).name
        with (run/'sources'/name).open('xb') as f:f.write(original)
        with (run/'songs'/name).open('x',encoding='utf-8') as f:f.write(candidate)
        record=dict(row,output='songs/'+name,outputSha256=sha(candidate.encode()),embeddedEquality=True,
                    runtimeReview='pending',manualReview='pending',approved=False)
        records.append(record)
        table.append('<tr><td>'+html.escape(row.get('title',name))+'</td><td><a href="sources/'+name+'">ต้นฉบับ</a> · <a href="songs/'+name+'">ฉบับใหม่</a></td><td>'+str(row.get('bars',''))+'</td><td>รอ Ti ตรวจ</td><td>'+html.escape('; '.join(row['issues']))+'</td></tr>')
    (run/'index.html').write_text('<!doctype html><meta charset="utf-8"><title>Batch review</title><h1>สำเนาสำหรับตรวจ — ยังไม่อนุมัติ</h1><p>ข้อมูลที่ย้ายเหมือนต้นฉบับ ไม่ได้ยืนยันว่าต้นฉบับถูกต้อง รายการนี้ไม่บันทึกการอนุมัติอัตโนมัติ</p><table><tr><th>เพลง</th><th>เปรียบเทียบ</th><th>ห้อง</th><th>สถานะ</th><th>ข้อสังเกต</th></tr>'+''.join(table)+'</table>',encoding='utf-8')
    # A run without a final manifest is incomplete, never ready for review/promotion.
    (run/'manifest.json').write_text(dump({'planSha256':sha(raw),'templateSha256':plan['templateSha256'],
         'gitHeadAtExecution':git('rev-parse','HEAD'),'promotionAllowed':False,'songs':records}))
    return run

def verify(run):
    data=json.loads((run/'manifest.json').read_text())
    for row in data['songs']:
        src=(run/'sources'/Path(row['source']).name).read_bytes()
        out=(run/row['output']).read_bytes()
        if sha(src)!=row['sourceSha256'] or sha(out)!=row['outputSha256']:raise ValueError('review artifact changed: '+row['source'])
        transfer.assert_equal(transfer.snapshot(src.decode()),transfer.snapshot(out.decode()))
    return len(data['songs'])

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);sub=p.add_subparsers(dest='action',required=True)
    q=sub.add_parser('plan');q.add_argument('--band',default='all');q.add_argument('--output',type=Path,required=True);q.add_argument('--template',type=Path,default=TEMPLATE)
    q=sub.add_parser('execute');q.add_argument('plan',type=Path);q.add_argument('--expected-plan-sha256',required=True)
    q=sub.add_parser('verify');q.add_argument('run',type=Path)
    a=p.parse_args()
    try:
        if a.action=='plan':
            plan=make_plan(a.band,a.template);out=inside(a.output);out.parent.mkdir(parents=True,exist_ok=True)
            with out.open('x',encoding='utf-8') as f:f.write(dump(plan))
            print(f'Plan: {out}; songs={len(plan["songs"])}; templateClean={plan["templateCleanAtPlanning"]}')
        elif a.action=='execute':print(execute(a.plan,a.expected_plan_sha256))
        else:print(f'PASS: {verify(a.run)} review copies; musical approval remains pending')
    except (ValueError,OSError,KeyError) as exc:p.exit(1,str(exc)+'\n')
