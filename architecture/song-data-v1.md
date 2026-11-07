# Git revision architecture — implementation checkpoint

Status: synthetic-only implementation; actual GitHub recovery and production promotion blocked.
This supersedes the draft contracts in 3b1af0a. Governance is exclusively AGENTS.md.

## Decisions

The durable authority is one remote Git repository. Local state is disposable only
when the corresponding exact commits and required history are verified remotely.
Draft branches retain unapproved revisions without changing canonical selection or
publishing. A local test remote proves transaction mechanics, not cloud durability.

Future canonical song-data files are pointers to immutable full objects in
song-revisions. No duplicate editable payload lives in catalog, index or release.
All existing HTML sources remain untouched pending synthetic/recovery/pilot gates.

## Fingerprints

- contentHash: metadata, sections, footer, settings, and extensions (including unknowns).
- revisionHash: complete revision, including identity, schema and provenance/parent.
- artifact hash: exact generated file bytes; editor changes may change this only.
- contentRevision: increments on protected content change, never on no-change export.
- schema/editor/index/build versions describe separate contracts; hashes pin exact bytes.

Fingerprint encoding is `bandsheet-c14n-1`, implemented in Python and JavaScript:
type-tagged JSON, UTF-8 object-key ordering, no Unicode/text normalization, finite
binary64 numbers encoded as big-endian 16-digit hexadecimal, signed zero normalized.
Integral values must be within JS safe-integer bounds. Duplicate JSON keys, unpaired
surrogates and non-finite/out-of-domain numbers are rejected. This encoding is for
hashing only; full documents remain ordinary JSON. This deliberately supersedes the
original draft's ambiguous Python JSON byte encoding. Existing content-lock hashes
are a separate legacy protocol and are neither migrated nor refreshed.

Schemas are enforced by a local fail-closed validator for the repository's explicit
keyword subset, plus domain validation. It is not a general JSON Schema implementation.
Unknown song envelope fields are rejected; nested extension data is retained/hashed.

## Save transaction

Request: saveId, songId, expectedParentHash, full protected payload. Server owns
revision sequencing and provenance capture. A reused saveId with different bytes
fails; same request returns the original receipt. No-change uses the existing object.

The synthetic writer uses a dedicated bare repo and separate bare local test remote.
It writes immutable objects + draft pointer + receipt in one Git tree/commit, then
CAS-updates its local ref. A non-force push updates only drafts/synthetic-review.
It fetches remote objects, verifies ancestry and re-reads receipt/revision hashes
before returning `verified-test-remote`. Local crashes before ref update leave the
old head; after ref update, retry reuses the committed receipt. Divergent writers
stop and preserve their branches. No canonical pointers or approvals are written.

Network remotes and normal project repos are intentionally rejected. Actual remote
transport, authorization, draft branch deployment isolation and credentials must be
reviewed before introducing a network-enabled writer. Nothing in this lab authorizes it.

## Browser adapter

The frozen rc.1 template is read without modification. The derived synthetic page
embeds the whole revision and replaces Save with the protocol above. It removes the
startup font assignment and render-time rowSizes insertion that changed source data.
Metadata/chord/lyric edits still use the existing Luminous editor interactions.

Recovery records are per page instance. Multiple local drafts require explicit
selection, never last-write-wins. Storage is a recovery cache, not durable authority.
Export produces a recovery JSON bundle, never an approved revision or a Git Save.
A pending retry preserves its saveId; later edits remain dirty after acknowledgment.

## Catalog / approval / release

Catalog reads revisions and relationships, checks duplicate IDs/URLs/references,
and emits detached JSON. Its hash excludes UI/release labels. Matching approval
records are labelled unverified; the builder cannot declare user approval.
Release schema pins input commit, revision hashes, UI/build hashes, catalog and
artifacts, verification references and previous release. No promotionAllowed flag.
Promotion and rollback executors are not implemented in this checkpoint.

## Recovery and retirement

Project source, schema, required assets/dependencies, selected/unapproved revisions,
provenance and decisions must be recoverable from authorized remote Git refs.
A full independent clone must build/open/verify them before local deletion is safe.
Deleting only a synthetic writer clone is a narrower test and must be reported so.

The source worktree shares the original project's .git. The original project has
local-only files (inventory in verification/2026-11-06-architecture/inventory.json).
No cleanup is authorized to discard them. Superseded workflow files remain present
until the remote checkpoint and dependency gates permit reviewed deletion.

## Reproduction

Python 3.9+ standard library, Git, Node 22+ and Chromium are required. No npm/pip
installation is needed. Browser tests use CHROME_BIN when not on the default macOS
Chrome path. Run the exact synthetic commands in AGENTS.md. All lab state is under
a newly created temporary directory; init rejects an existing target directory.

For interactive synthetic review only:

    python3 -B tools/synthetic_save_lab.py init --directory /tmp/bandsheet-new-lab
    python3 -B tools/synthetic_save_lab.py serve --repo /tmp/bandsheet-new-lab/writer.git

The server prints its loopback URL. This is not the public website, a production
backend, a real-song intake tool, or a backup of the project.
