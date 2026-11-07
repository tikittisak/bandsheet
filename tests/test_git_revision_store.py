import copy
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src/intake'))
from git_store import Writer, StoreError, Conflict, initialize_lab, git, read, commit_files, REF
import song_data_contract as c


class GitRevisionStoreTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix='bandsheet-git-test-')
        self.folder=Path(self.temp.name)/'lab'
        self.fixture=c.load_json(ROOT/'tests/fixtures/song-data/representative.json')
        self.repo=initialize_lab(self.folder,self.fixture)
        self.writer=Writer(self.repo)

    def tearDown(self):
        self.temp.cleanup()

    def request(self,base=None,save_id='save-test-0001'):
        base=base or self.writer.current(self.fixture['songId'])
        return {'saveId':save_id,'songId':base['songId'],'expectedParentHash':c.revision_hash(base),'payload':copy.deepcopy(c.semantic_payload(base))}

    def test_no_change_and_duplicate_save_are_idempotent(self):
        req=self.request()
        first=self.writer.save(req)
        again=self.writer.save(req)
        self.assertEqual(first,again)
        self.assertFalse(first['changed'])
        self.assertEqual(first['revision'],self.fixture)
        self.assertEqual(self.writer.verify()['revisions'],1)
        next_receipt=self.writer.save(self.request(save_id='save-test-0002'))
        self.assertEqual(next_receipt['revisionHash'],first['revisionHash'])
        self.assertNotEqual(next_receipt['saveCommit'],first['saveCommit'])

    def test_every_protected_family_changes_hash_and_preserves_other_fields(self):
        mutations=[lambda p:p['metadata'].update(title='Edited synthetic title'),
                   lambda p:p['sections'][0]['bars'][0].update(c='Dm'),
                   lambda p:p['sections'][1].update(cols=['Edited synthetic lyric']),
                   lambda p:p['sections'].reverse(),
                   lambda p:p['footer'].update(notes=['Edited footer']),
                   lambda p:p['settings'].update(transpose=1),
                   lambda p:p['extensions'].update(future={'unknown':[True,2.5]})]
        for index,mutation in enumerate(mutations):
            base=self.writer.current(self.fixture['songId'])
            req=self.request(base,save_id=f'save-family-{index:04}')
            mutation(req['payload'])
            result=self.writer.save(req)
            self.assertEqual(c.semantic_payload(result['revision']),req['payload'])
            self.assertNotEqual(result['contentHash'],c.content_hash(base))
            self.assertEqual(result['revision']['provenance']['parentRevisionHash'],c.revision_hash(base))
            self.assertEqual(result['revision']['contentRevision'],base['contentRevision']+1)
            self.assertEqual(result['revision']['provenance']['sourceRef'],base['provenance']['sourceRef'])
            self.assertEqual(result['approval'],'unapproved')
        self.assertEqual(self.writer.verify()['revisions'],8)

    def test_stale_parent_and_reused_save_id_do_not_overwrite(self):
        first=self.request();second=self.request(save_id='save-other-0002')
        first['payload']['metadata']['title']='First edit'
        self.writer.save(first)
        tip=git(self.repo,'rev-parse',REF)
        with self.assertRaises(Conflict):self.writer.save(second)
        first['payload']['metadata']['title']='Different edit same ID'
        with self.assertRaises(Conflict):self.writer.save(first)
        self.assertEqual(git(self.repo,'rev-parse',REF),tip)

    def test_crash_process_at_each_transaction_boundary_and_retry(self):
        for index,stage in enumerate(('before-commit','before-local-ref','after-local-ref','before-push','after-push')):
            req=self.request(save_id=f'save-crash-{index:04}')
            req['payload']['metadata']['title']=stage
            script="import sys,os,json;sys.path.insert(0,sys.argv[1]);from git_store import Writer;w=Writer(sys.argv[2],fault=lambda s:os._exit(71) if s==sys.argv[3] else None);w.save(json.loads(sys.stdin.read()))"
            result=subprocess.run([sys.executable,'-B','-c',script,str(ROOT/'src/intake'),str(self.repo),stage],input=json.dumps(req),text=True)
            self.assertEqual(result.returncode,71)
            recovered=Writer(self.repo).save(req)
            self.assertEqual(recovered['revision']['metadata']['title'],stage)
            self.assertEqual(Writer(self.repo).save(req),recovered)
            self.writer.verify()

    def test_remote_missing_does_not_acknowledge(self):
        req=self.request();req['payload']['metadata']['title']='Offline edit'
        remote=self.folder/'remote.git';offline=self.folder/'offline.git'
        remote.rename(offline)
        try:
            with self.assertRaises(StoreError):self.writer.save(req)
        finally:offline.rename(remote)
        self.assertEqual(self.writer.save(req)['persistence'],'verified-test-remote')

    def test_fresh_clone_after_deleting_writer_recovers_exact_history(self):
        req=self.request();req['payload']['metadata']['title']='Recover from remote'
        saved=self.writer.save(req)
        shutil.rmtree(self.repo)
        subprocess.run(['git','clone','--bare','--no-local',str(self.folder/'remote.git'),str(self.repo)],check=True,capture_output=True)
        fresh=Writer(self.repo)
        self.assertEqual(fresh.current(req['songId']),saved['revision'])
        self.assertEqual(fresh.save(req),saved)
        self.assertEqual(fresh.verify()['revisions'],2)
        self.assertFalse((self.repo/'objects/info/alternates').exists())

    def test_remote_payload_tamper_stops(self):
        digest=c.revision_hash(self.fixture)
        bad=copy.deepcopy(self.fixture);bad['metadata']['title']='Tampered'
        remote=self.folder/'remote.git';parent=git(remote,'rev-parse',REF)
        commit=commit_files(remote,parent,{f'song-revisions/{bad["songId"]}/{digest}.json':bad})
        git(remote,'update-ref',REF,commit,parent)
        with self.assertRaisesRegex(StoreError,'integrity'):self.writer.verify()

    def test_real_song_paths_and_approval_fields_are_rejected(self):
        req=self.request();req['songId']='hysteria'
        with self.assertRaises(StoreError):self.writer.save(req)
        req=self.request();req['approved']=True
        with self.assertRaises(StoreError):self.writer.save(req)
        with self.assertRaises(StoreError):Writer(ROOT)
        with self.assertRaises(StoreError):initialize_lab(self.folder,self.fixture)

    def test_forged_hash_or_missing_payload_field_is_rejected(self):
        req=self.request();req['expectedParentHash']='0'*64
        with self.assertRaises(Conflict):self.writer.save(req)
        req=self.request();del req['payload']['extensions']
        with self.assertRaises(StoreError):self.writer.save(req)
