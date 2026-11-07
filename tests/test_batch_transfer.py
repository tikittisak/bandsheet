import copy
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
spec=importlib.util.spec_from_file_location('batch',ROOT/'tools/batch_transfer.py')
b=importlib.util.module_from_spec(spec);spec.loader.exec_module(b)

class BatchTransferTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name).resolve()
        (self.root/'songs').mkdir();(self.root/'bands').mkdir()
        for name in ('a.html','b.html'):
            (self.root/'songs'/name).write_bytes((ROOT/'_archive/prototypes/preview-luminous-v7.0.0-alpha.2.html').read_bytes())
        (self.root/'bands/tmj.json').write_text(json.dumps({'songs':['a.html','b.html']}))
        path=self.root/b.TEMPLATE;path.parent.mkdir(parents=True);path.write_bytes((ROOT/b.TEMPLATE).read_bytes())
        self.ctx=patch.multiple(b,ROOT=self.root)
        self.ctx.start();self.addCleanup(self.ctx.stop)
        self.g=patch.object(b,'git',return_value='a'*40);self.g.start();self.addCleanup(self.g.stop)
        self.clean=patch.object(b,'template_clean',return_value=True);self.clean.start();self.addCleanup(self.clean.stop)
        self.plan=b.make_plan('all');self.path=self.root/'plan.json';self.path.write_text(b.dump(self.plan))

    def execute(self):return b.execute(self.path,b.sha(self.path.read_bytes()))

    def test_lossless_review_copies_never_approved(self):
        before={p.name:p.read_bytes() for p in (self.root/'songs').iterdir()}
        run=self.execute();self.assertEqual(b.verify(run),2)
        records=json.loads((run/'manifest.json').read_text())['songs']
        self.assertTrue(all(r['manualReview']=='pending' and not r['approved'] for r in records))
        self.assertEqual(before,{p.name:p.read_bytes() for p in (self.root/'songs').iterdir()})
        self.assertFalse((self.root/'content-locks.json').exists())

    def test_later_source_change_aborts_entire_batch_before_write(self):
        with (self.root/'songs/b.html').open('a') as f:f.write('changed')
        with self.assertRaisesRegex(ValueError,'source changed'):self.execute()
        self.assertFalse((self.root/'_work').exists())

    def test_template_change_stops(self):
        with (self.root/b.TEMPLATE).open('a') as f:f.write('changed')
        with self.assertRaisesRegex(ValueError,'template changed'):self.execute()

    def test_uncommitted_template_stops(self):
        with patch.object(b,'template_clean',return_value=False):
            with self.assertRaisesRegex(ValueError,'uncommitted'):self.execute()

    def test_wrong_plan_and_library_hash_stops(self):
        with self.assertRaisesRegex(ValueError,'plan hash'):b.execute(self.path,'0'*64)
        self.plan['transferLibrarySha256']='0'*64;self.path.write_text(b.dump(self.plan))
        with self.assertRaisesRegex(ValueError,'code changed'):self.execute()

    def test_unknown_fields_preserved_and_review_tamper_detected(self):
        run=self.execute();manifest=json.loads((run/'manifest.json').read_text())
        row=manifest['songs'][0];path=run/row['output']
        text=path.read_text().replace('value="135"','value="999"',1);path.write_text(text)
        row['outputSha256']=b.sha(text.encode())
        (run/'manifest.json').write_text(b.dump(manifest))
        with self.assertRaisesRegex(ValueError,'semantic divergence'):b.verify(run)

    def test_duplicate_and_outside_target_stops(self):
        for source in ('../outside.html','bands/tmj.json'):
            plan=copy.deepcopy(self.plan);plan['songs'][0]['source']=source
            with self.assertRaises(ValueError):b.preflight(plan)
        plan=copy.deepcopy(self.plan);plan['songs'].append(plan['songs'][0])
        with self.assertRaisesRegex(ValueError,'duplicate'):b.preflight(plan)

if __name__=='__main__':unittest.main()
