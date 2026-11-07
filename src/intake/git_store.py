"""Synthetic-only Git persistence lab. Cannot write a normal project or network remote.

All state is committed Git objects. A local ref is a retry cache; only verified
remote ancestry + receipt/revision bytes acknowledge Save. No canonical promotion.
"""
import copy
import fcntl
import json
import os
import re
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools'))
import song_data_contract as contract

REF = 'refs/heads/drafts/synthetic-review'
FETCH_REF = 'refs/remotes/origin/synthetic-review'
FORMAT = {'format': 'bandsheet-synthetic-store-1', 'syntheticOnly': True}
HASH = re.compile(r'^[0-9a-f]{64}$')
SAVE_ID = re.compile(r'^[a-zA-Z0-9][a-zA-Z0-9-]{7,79}$')


class StoreError(ValueError):
    pass


class Conflict(StoreError):
    pass


def git(repo, *args, data=None, env=None, check=True):
    options = dict(os.environ, GIT_TERMINAL_PROMPT='0', GIT_CONFIG_NOSYSTEM='1')
    if env:
        options.update(env)
    result = subprocess.run(['git', '--git-dir='+str(repo), *args], input=data, text=True,
                            capture_output=True, env=options, timeout=30)
    if check and result.returncode:
        raise StoreError(result.stderr.strip() or 'Git operation failed')
    return result.stdout.strip() if check else result


def read(repo, ref, path):
    return contract.parse_json(git(repo, 'show', f'{ref}:{path}'))


def commit_files(repo, parent, files):
    with tempfile.TemporaryDirectory(prefix='bandsheet-index-') as folder:
        env = {'GIT_INDEX_FILE': str(Path(folder)/'index'),
               'GIT_AUTHOR_NAME': 'Bandsheet Synthetic Writer', 'GIT_AUTHOR_EMAIL': 'synthetic@invalid',
               'GIT_COMMITTER_NAME': 'Bandsheet Synthetic Writer', 'GIT_COMMITTER_EMAIL': 'synthetic@invalid'}
        git(repo, 'read-tree', parent if parent else '--empty', env=env)
        for path, value in sorted(files.items()):
            blob = git(repo, 'hash-object', '-w', '--stdin', data=contract.document_json(value)+'\n')
            git(repo, 'update-index', '--add', '--cacheinfo', '100644', blob, path, env=env)
        tree = git(repo, 'write-tree', env=env)
        args = ['commit-tree', tree]
        if parent:
            args += ['-p', parent]
        return git(repo, *args, '-m', 'synthetic: capture unapproved revision', env=env)


def initialize_lab(folder, fixture):
    """Explicit new lab only; no existing directory, songs, credentials or public remote."""
    folder = Path(folder).resolve()
    if folder.exists():
        raise StoreError('lab directory already exists')
    contract.validate_song(fixture)
    if not fixture['songId'].startswith('fixture-') or fixture['provenance']['sourceType'] != 'synthetic-fixture' or fixture['provenance']['parentRevisionHash'] is not None:
        raise StoreError('only a synthetic root fixture may initialize a lab')
    folder.mkdir(parents=True)
    remote = folder/'remote.git'
    subprocess.run(['git','init','--bare',str(remote)],check=True,capture_output=True)
    digest = contract.revision_hash(fixture)
    files = {'storage-format.json': FORMAT,
             f"song-revisions/{fixture['songId']}/{digest}.json": fixture,
             f"draft-heads/{fixture['songId']}.json": {'songId':fixture['songId'],'revisionHash':digest}}
    commit = commit_files(remote, None, files)
    git(remote,'update-ref',REF,commit)
    git(remote,'symbolic-ref','HEAD',REF)
    local = folder/'writer.git'
    subprocess.run(['git','clone','--bare','--no-local',str(remote),str(local)],check=True,capture_output=True)
    return local


class Writer:
    def __init__(self, repo, fault=None):
        self.repo = Path(repo).resolve()
        self.fault = fault or (lambda stage: None)
        if git(self.repo,'rev-parse','--is-bare-repository') != 'true':
            raise StoreError('writer requires a dedicated bare synthetic repository')
        remote = git(self.repo,'remote','get-url','origin')
        if not os.path.isabs(remote) or not Path(remote).is_dir():
            raise StoreError('network remotes are disabled in this synthetic lab')
        self.remote = Path(remote).resolve()
        if self.remote == self.repo or git(self.remote,'rev-parse','--is-bare-repository') != 'true':
            raise StoreError('remote must be a separate bare test repository')
        if read(self.repo,REF,'storage-format.json') != FORMAT or read(self.remote,REF,'storage-format.json') != FORMAT:
            raise StoreError('not a synthetic store')

    def lock(self):
        return open(self.repo/'bandsheet-writer.lock','a')

    def sync(self):
        # Fetch actual remote objects before inspecting a receipt. No cached ls-remote assertion.
        git(self.repo,'fetch','--no-tags','origin',f'{REF}:{FETCH_REF}')
        remote = git(self.repo,'rev-parse',FETCH_REF)
        local = git(self.repo,'rev-parse',REF)
        if local != remote:
            if git(self.repo,'merge-base','--is-ancestor',local,remote,check=False).returncode == 0:
                git(self.repo,'update-ref',REF,remote,local)
                local = remote
            elif git(self.repo,'merge-base','--is-ancestor',remote,local,check=False).returncode != 0:
                raise Conflict('divergent remote/local drafts; preserve both and review')
        return local

    def current(self, song_id, sync=True):
        if not isinstance(song_id,str) or not contract.SONG_ID_RE.fullmatch(song_id) or not song_id.startswith('fixture-'):
            raise StoreError('synthetic songId required')
        with self.lock() as lock:
            fcntl.flock(lock,fcntl.LOCK_EX)
            ref = self.sync() if sync else REF
            return self._current(ref,song_id)

    def _revision(self, ref, song_id, digest):
        if not isinstance(digest,str) or not HASH.fullmatch(digest):
            raise StoreError('invalid revision hash')
        song = read(self.repo,ref,f'song-revisions/{song_id}/{digest}.json')
        contract.validate_song(song)
        if song['songId'] != song_id or contract.revision_hash(song) != digest:
            raise StoreError('revision integrity failure')
        return song

    def _current(self, ref, song_id):
        pointer = read(self.repo,ref,f'draft-heads/{song_id}.json')
        if set(pointer) != {'songId','revisionHash'} or pointer['songId'] != song_id:
            raise StoreError('invalid draft pointer')
        return self._revision(ref,song_id,pointer['revisionHash'])

    def save(self, request):
        contract.canonical(request)
        if not isinstance(request,dict) or set(request) != {'saveId','songId','expectedParentHash','payload'}:
            raise StoreError('unexpected Save envelope fields')
        save_id, song_id = request['saveId'],request['songId']
        if not isinstance(save_id,str) or not SAVE_ID.fullmatch(save_id):
            raise StoreError('invalid saveId')
        if not isinstance(song_id,str) or not contract.SONG_ID_RE.fullmatch(song_id) or not song_id.startswith('fixture-'):
            raise StoreError('synthetic songId required')
        payload = request['payload']
        if not isinstance(payload,dict) or set(payload) != {'metadata','sections','footer','settings','extensions'}:
            raise StoreError('full protected payload required')
        request_hash = contract.sha256(contract.canonical(request))
        receipt_path = f'save-receipts/{save_id}.json'
        with self.lock() as lock:
            fcntl.flock(lock,fcntl.LOCK_EX)
            tip = self.sync()
            prior = git(self.repo,'cat-file','-e',f'{tip}:{receipt_path}',check=False)
            if prior.returncode == 0:
                receipt = read(self.repo,tip,receipt_path)
                if receipt.get('requestHash') != request_hash:
                    raise Conflict('saveId already belongs to another request')
                return self._ack(receipt_path,receipt)
            base = self._current(tip,song_id)
            if request['expectedParentHash'] != contract.revision_hash(base):
                raise Conflict('stale parent; draft retained, no overwrite')
            candidate = copy.deepcopy(base)
            candidate.update(copy.deepcopy(payload))
            contract.validate_song(candidate)
            changed = contract.canonical(contract.semantic_payload(candidate)) != contract.canonical(contract.semantic_payload(base))
            if changed:
                candidate['contentRevision'] = base['contentRevision']+1
                candidate['provenance'].update(parentRevisionHash=contract.revision_hash(base),
                    sourceType='synthetic-browser',capturedOn=datetime.now(timezone.utc).date().isoformat())
            else:
                candidate = base  # Preserve original bytes, including absent optional fields.
            digest = contract.revision_hash(candidate)
            revision_path = f'song-revisions/{song_id}/{digest}.json'
            receipt = {'format':'bandsheet-save-receipt-1','saveId':save_id,'songId':song_id,
                       'requestHash':request_hash,'revisionHash':digest,'contentHash':contract.content_hash(candidate),
                       'parentRevisionHash':candidate['provenance']['parentRevisionHash'],'changed':changed,
                       'approval':'unapproved','remoteRef':REF}
            files = {receipt_path:receipt,f'draft-heads/{song_id}.json':{'songId':song_id,'revisionHash':digest}}
            if changed:
                exists = git(self.repo,'cat-file','-e',f'{tip}:{revision_path}',check=False)
                if exists.returncode == 0:
                    if read(self.repo,tip,revision_path) != candidate:
                        raise StoreError('immutable revision collision')
                else:
                    files[revision_path] = candidate
            self.fault('before-commit')
            commit = commit_files(self.repo,tip,files)
            self.fault('before-local-ref')
            git(self.repo,'update-ref',REF,commit,tip)  # Compare-and-swap; no partial tree is selected.
            self.fault('after-local-ref')
            return self._ack(receipt_path,receipt)

    def _ack(self, path, receipt):
        tip = git(self.repo,'rev-parse',REF)
        self.fault('before-push')
        git(self.repo,'push','origin',f'{tip}:{REF}')  # Never force; concurrent writers conflict.
        self.fault('after-push')
        git(self.repo,'fetch','--no-tags','origin',f'{REF}:{FETCH_REF}')
        if git(self.repo,'merge-base','--is-ancestor',tip,FETCH_REF,check=False).returncode:
            raise StoreError('remote does not contain saved commit')
        verified = read(self.repo,FETCH_REF,path)
        if verified != receipt:
            raise StoreError('remote receipt differs')
        revision = self._revision(FETCH_REF,receipt['songId'],receipt['revisionHash'])
        if contract.content_hash(revision) != receipt['contentHash']:
            raise StoreError('remote content fingerprint differs')
        save_commit = git(self.repo,'log','-1','--format=%H',FETCH_REF,'--',path)
        return dict(receipt,revision=revision,saveCommit=save_commit,persistence='verified-test-remote')

    def verify(self):
        with self.lock() as lock:
            fcntl.flock(lock,fcntl.LOCK_EX)
            self.sync()
            paths = git(self.repo,'ls-tree','-r','--name-only',FETCH_REF).splitlines()
            count = 0
            for path in paths:
                if path.startswith('song-revisions/'):
                    _,song_id,filename = path.split('/')
                    song = self._revision(FETCH_REF,song_id,filename.removesuffix('.json'))
                    parent = song['provenance']['parentRevisionHash']
                    if parent:
                        prev = self._revision(FETCH_REF,song_id,parent)
                        if song['contentRevision'] != prev['contentRevision']+1:
                            raise StoreError('revision sequence mismatch')
                    elif song['contentRevision'] != 1 or song['provenance']['sourceType'] != 'synthetic-fixture':
                        raise StoreError('invalid synthetic root')
                    count += 1
                elif path.startswith('draft-heads/'):
                    self._current(FETCH_REF,Path(path).stem)
                elif path.startswith('save-receipts/'):
                    receipt = read(self.repo,FETCH_REF,path)
                    song = self._revision(FETCH_REF,receipt['songId'],receipt['revisionHash'])
                    if receipt['contentHash'] != contract.content_hash(song) or receipt['approval'] != 'unapproved':
                        raise StoreError('invalid receipt')
                elif path != 'storage-format.json':
                    raise StoreError('unexpected file in synthetic store')
            return {'revisions':count,'remoteCommit':git(self.repo,'rev-parse',FETCH_REF),
                    'authority':'local-test-remote-only','productionApproved':False}
