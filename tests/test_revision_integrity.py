import copy
import json
from pathlib import Path
import subprocess
import sys
import unittest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
import song_data_contract as c


class RevisionIntegrityTests(unittest.TestCase):
    def setUp(self):
        self.song=c.load_json(ROOT/'tests/fixtures/song-data/representative.json')
        self.band=c.load_json(ROOT/'tests/fixtures/catalog/band.json')
        self.playlist=c.load_json(ROOT/'tests/fixtures/catalog/playlist.json')

    def test_python_javascript_canonical_vectors(self):
        vectors=[None,True,False,1,1.0,-0.0,.25,1e-7,9007199254740991,{'𐀀':'ไทย','\ue000':'é'},self.song]
        script="require('node:vm').runInThisContext(require('node:fs').readFileSync(process.argv[1],'utf8'));const vs=JSON.parse(require('node:fs').readFileSync(0,'utf8'));process.stdout.write(JSON.stringify(vs.map(RevisionProtocol.canonical)))"
        actual=json.loads(subprocess.check_output(['node','-e',script,str(ROOT/'src/sheet/revision-client.js')],input=json.dumps(vectors),text=True))
        self.assertEqual(actual,[c.canonical(v) for v in vectors])
        self.assertEqual(c.canonical(1),c.canonical(1.0))
        self.assertEqual(c.canonical(0),c.canonical(-0.0))

    def test_invalid_contract_values_fail_closed(self):
        mutations=[lambda s:s.update(schemaVersion=True),lambda s:s['provenance'].update(capturedOn='2026-99-99'),
            lambda s:s['sections'][0].update(bars=[None]),lambda s:s['settings'].update(transpose=float('nan')),
            lambda s:s['settings'].update(transpose=10**1000),lambda s:s['sections'][0].update(rowSizes=[True]),
            lambda s:s['sections'][1].update(cols=[None]),lambda s:s['metadata'].update(title='\ud800')]
        for change in mutations:
            with self.subTest(change=change):
                song=copy.deepcopy(self.song);change(song)
                with self.assertRaises(c.ContractError):c.validate_song(song)
        for raw in ('{"a":1,"a":2}','{"a":NaN}','{"a":Infinity}'):
            with self.assertRaises(c.ContractError):c.parse_json(raw)

    def test_extensions_are_protected_and_approval_is_not_authority(self):
        changed=copy.deepcopy(self.song);changed['extensions']['fixtureUnknownField']['preserve']=False
        self.assertNotEqual(c.content_hash(changed),c.content_hash(self.song))
        record={'songId':self.song['songId'],'revisionHash':c.revision_hash(self.song),'contentHash':c.content_hash(self.song),'approvedBy':'Ti'}
        catalog=c.build_catalog([self.song],[self.band],[self.playlist],{self.song['songId']:record},'a','b')
        self.assertNotEqual(catalog['songs'][0]['approvalStatus'],'approved')

    def test_duplicate_routes_and_playlist_ids_rejected(self):
        song=copy.deepcopy(self.song);song['songId']='fixture-another'
        with self.assertRaisesRegex(c.ContractError,'slug'):c.build_catalog([self.song,song],[self.band],[self.playlist],{},'a','b')
        with self.assertRaisesRegex(c.ContractError,'playlistId'):c.build_catalog([self.song],[self.band],[self.playlist,self.playlist],{},'a','b')

    def test_catalog_independent_of_ui_versions_and_mutable_inputs(self):
        a=c.build_catalog([self.song],[self.band],[self.playlist],{},'editor-a','release-a')
        b=c.build_catalog([self.song],[self.band],[self.playlist],{},'editor-b','release-b')
        self.assertEqual(a,b)
        self.song['metadata']['title']='Later mutation'
        self.assertNotEqual(a['songs'][0]['metadata']['title'],self.song['metadata']['title'])

    def test_template_change_preserves_entire_revision(self):
        template=(ROOT/'releases/luminous-v7.0.0-rc.1/template.html').read_text()
        first=c.render_song_html(template,self.song,'synthetic.1')
        second=c.render_song_html(template.replace('</head>','<style>/* synthetic UI change */</style></head>'),self.song,'synthetic.2')
        self.assertNotEqual(c.sha256(first),c.sha256(second))
        for page in (first,second):
            data=c.extract_rendered_payload(page)
            self.assertEqual(data['revision'],self.song)
            self.assertEqual({k:data[k] for k in c.semantic_payload(self.song)},c.semantic_payload(self.song))
            self.assertEqual(data['sheetMeta']['revisionHash'],c.revision_hash(self.song))

    def test_duplicate_template_data_block_stops(self):
        template=(ROOT/'releases/luminous-v7.0.0-rc.1/template.html').read_text()
        template+='\nvar SETTINGS = {};\n// ── END SETTINGS ──\n'
        with self.assertRaises(c.ContractError):c.render_song_html(template,self.song,'test')
