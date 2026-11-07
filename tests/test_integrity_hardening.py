import contextlib
import copy
import importlib.util
import io
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('hardening_guard',ROOT/'content_guard.py')
g=importlib.util.module_from_spec(spec);spec.loader.exec_module(g)


class IntegrityHardening(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.doc=(ROOT/'_archive/prototypes/preview-luminous-v7.0.0-alpha.2.html').read_text()

    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name);(self.root/'songs').mkdir()
        self.song=self.root/'songs/resistance.html';self.song.write_text(self.doc)
        self.locks=self.root/'content-locks.json';self.locks.write_text('{"version":1,"songs":{}}')

    def command(self, doc=None, args=(), baseline_locks=None):
        if doc is not None:self.song.write_text(doc)
        def baseline(path):
            return self.doc if path=='songs/resistance.html' else json.dumps(baseline_locks or {'version':1,'songs':{}})
        with patch.multiple(g,ROOT=self.root,SONGS=self.root/'songs',LOCKS_PATH=self.locks),patch.object(g,'head_text',side_effect=baseline),patch.object(g,'tracked_song_paths',return_value={'songs/resistance.html'}),patch('sys.argv',['guard',*args]),contextlib.redirect_stdout(io.StringIO()):
            return g.main()

    def test_css_only_passes(self):
        self.assertEqual(self.command(self.doc.replace('</style>','.audit{color:red}</style>',1)),0)

    def test_mutations_and_exact_allow(self):
        for kind in ('chord','lyric','structure','metadata','settings','footer','revision'):
            with self.subTest(kind=kind):
                doc=self.doc
                if kind=='metadata':doc=doc.replace('value="135"','value="999"',1)
                else:
                    name,marker=('SHEET_META','SHEET META') if kind=='revision' else ('SETTINGS','SETTINGS') if kind=='settings' else ('FOOTER','FOOTER') if kind=='footer' else ('SECTIONS','DATA')
                    value=copy.deepcopy(g.json_var(doc,name,f'// ── END {marker} ──'))
                    if kind=='chord':next(s for s in value if s.get('bars'))['bars'][0]['c']='AUDIT'
                    elif kind=='lyric':next(s for s in value if s.get('type')=='note')['cols'][0]='AUDIT'
                    elif kind=='structure':value.reverse()
                    elif kind=='settings':value['transpose']=11
                    elif kind=='revision':value['sheetRevision']+=1
                    else:value['notes']=['AUDIT']
                    end=doc.index(f'// ── END {marker} ──');start=doc.rfind(f'var {name} = ',0,end)
                    doc=doc[:start]+f'var {name} = '+json.dumps(value)+';\n'+doc[end:]
                self.assertNotEqual(doc,self.doc)
                self.assertEqual(self.command(doc),1)
                self.assertEqual(self.command(doc,('--allow-content','songs/resistance.html')),0)

    def test_runtime_mutation_not_covered_by_content_allow(self):
        doc=self.doc.replace('</body>','<script>SECTIONS[0].bars[0].c="AUDIT";</script></body>')
        self.assertEqual(self.command(doc),1)

    def test_unquoted_handlers_and_script_urls_blocked(self):
        for markup in ('<img src=x onerror=SECTIONS.pop()>',
                       '<a href="java&#x0a;script:SECTIONS.pop()">test</a>',
                       '<iframe srcdoc="test"></iframe>'):
            with self.subTest(markup=markup):
                self.assertEqual(self.command(self.doc.replace('</body>',markup+'</body>')),1)

    def test_deleted_lock_cannot_bypass(self):
        locks={'version':1,'songs':{'songs/resistance.html':{'sha256':g.content_digest(g.content_payload(self.doc))}}}
        self.assertEqual(self.command(baseline_locks=locks),1)

    def test_exact_allow_only(self):
        for name in ('songs/*.html','songs/','songs/resistance.html'):
            self.assertEqual(self.command(args=('--allow-content',name)),1)

    def test_importers_disabled(self):
        for name in ('bandsheet_import.py','import_edited_song_html.py','busk_import.py'):
            result=subprocess.run(['python3','-B',str(ROOT/name),'missing-input','--check'],capture_output=True,text=True)
            self.assertNotEqual(result.returncode,0)
            self.assertIn('suspended',result.stdout+result.stderr)

    def test_safe_export_preserves_literal_text(self):
        node=shutil.which('node')
        if not node:self.skipTest('Node unavailable')
        doc=(ROOT/'_archive/prototypes/preview-luminous-v7.0.0-alpha.2.html').read_text()
        fn=doc[doc.index('function injectData(html){'):doc.index('function cleanRuntimeHtml(html){')]
        marker='</script><script>globalThis.AUDIT=1</script>'
        code='var SECTIONS=[{bars:[{c:'+json.dumps(marker)+'}]}],FOOTER={},SETTINGS={},SHEET_META={};\n'+fn+'\nprocess.stdout.write(injectData('+json.dumps(self.doc)+'));'
        output=subprocess.check_output([node,'-e',code],text=True)
        self.assertNotIn(marker,output)
        self.assertEqual(g.json_var(output,'SECTIONS','// ── END DATA ──')[0]['bars'][0]['c'],marker)

    def test_trial_payload_unchanged_and_blank_is_empty(self):
        original = g.content_payload(self.doc)
        published = g.content_payload((ROOT/'songs/resistance.html').read_text(), 'songs/resistance.html')
        revision = published["published_review"]["revision"]
        self.assertEqual(original, {
            **{field: published[field] for field in ("metadata", "sections", "footer", "settings")},
            "sheet_meta": revision["extensions"]["legacyV619"]["sheetMeta"],
        })
        blank=g.content_payload((ROOT/'_archive/prototypes/luminous-v7.0.0-alpha.2-blank.html').read_text())
        self.assertTrue(all(not v for v in blank['metadata'].values()))
        self.assertEqual([b['c'] for b in blank['sections'][0]['bars']],['—']*4)
        self.assertEqual(blank['footer']['notes'],[])

    def test_export_title_is_escaped(self):
        doc=(ROOT/'_archive/prototypes/preview-luminous-v7.0.0-alpha.2.html').read_text()
        self.assertIn("auditEscape(fn+(ar?' '+ar:''))",doc)

    def test_push_entrypoints_reject_invalid_template(self):
        (self.root/'commands').mkdir()
        for rel in (
            'push.sh', 'commands/push-site.sh', 'commands/dry-run.sh',
            'validate_bandsheet.py', 'published_sheet.py',
        ):
            shutil.copy2(ROOT/rel,self.root/rel)
        (self.root/'_template.html').write_text('INVALID TEMPLATE')
        # Validation must stop before update_index or any Git operation exists.
        for entry in ('commands/dry-run.sh','commands/push-site.sh'):
            p=subprocess.run(['bash',entry,'--dry-run'],cwd=self.root,text=True,capture_output=True)
            self.assertNotEqual(p.returncode,0)
            self.assertIn('Bandsheet validator: FAIL',p.stdout)


if __name__=='__main__':unittest.main()
