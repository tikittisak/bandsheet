import copy
import importlib.util
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('transfer',ROOT/'tools/transfer_song_trial.py')
t=importlib.util.module_from_spec(spec);spec.loader.exec_module(t)


class TransferTrialTests(unittest.TestCase):
    def setUp(self):
        self.source=(ROOT/'_archive/prototypes/preview-luminous-v7.0.0-alpha.2.html').read_text()
        self.template=t.TEMPLATE.read_text()

    def test_lossless_including_revision(self):
        t.assert_equal(t.snapshot(self.source),t.snapshot(t.render(self.source,self.template)))

    def test_all_mutations_fail(self):
        original=t.snapshot(self.source)
        for kind in ('metadata','chord','lyric','structure','settings','footer','revision'):
            with self.subTest(kind=kind):
                changed=copy.deepcopy(original)
                if kind=='metadata':changed['metadata']['meta-key']='AUDIT'
                elif kind=='chord':next(s for s in changed['SECTIONS'] if s.get('bars'))['bars'][0]['c']='AUDIT'
                elif kind=='lyric':next(s for s in changed['SECTIONS'] if s.get('cols'))['cols'][0]='AUDIT'
                elif kind=='structure':changed['SECTIONS'].reverse()
                elif kind=='settings':changed['SETTINGS']['transpose']=11
                elif kind=='footer':changed['FOOTER']['notes']=['AUDIT']
                else:changed['SHEET_META']['sheetRevision']+=1
                with self.assertRaises(ValueError):t.assert_equal(original,changed)

    def test_unknown_fields_and_script_text_preserved(self):
        start,end,raw=t.span(self.source,'FOOTER')
        import json
        value=json.loads(raw);value['unknown']={'literal':'</script><script>TEST</script>','spaces':' x  y '}
        source=self.source[:start]+json.dumps(value)+';\n'+self.source[end:]
        output=t.render(source,self.template)
        self.assertNotIn('</script><script>TEST',output)
        t.assert_equal(t.snapshot(source),t.snapshot(output))

    def test_missing_duplicate_markers_stop(self):
        for doc in (self.template.replace('// ── END DATA ──','REMOVED'),self.template+'\n// ── END DATA ──'):
            with self.assertRaises(ValueError):t.render(self.source,doc)

    def test_hash_mismatch_writes_nothing(self):
        with self.assertRaises(ValueError):t.create_trial(ROOT/'songs/starlight.html','0'*64,'tmj')

    def test_explicit_template_mismatch_writes_nothing(self):
        source=ROOT/'songs/stockholm-syndrome.html'
        with self.assertRaisesRegex(ValueError,'template hash changed'):
            t.create_trial(source,t.sha(source.read_bytes()),'tmj','0'*64)

    def test_duplicate_json_keys_stop(self):
        source=self.source.replace('var FOOTER = {','var FOOTER = {"notes": [],',1)
        with self.assertRaises(ValueError):t.snapshot(source)


if __name__=='__main__':unittest.main()
