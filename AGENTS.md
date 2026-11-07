# Bandsheet — Git revision architecture transition

Updated: 2026-11-07. Authority: Ti's current instructions, then this file.

## Current authorization and boundaries

Ti authorized implementation of the audited transition plan on 2026-11-06.
Current work is recovery inventory, revised contracts, and synthetic browser/Git
persistence. This is not musical approval, production cutover, or push permission.

- Worktree: architecture/song-data-v1. Original draft baseline: 3b1af0ac8aad928ab7739a9806ff2d4dccd5e704.
- Do not change songs/*.html, existing indexes, bands, playlists, _template.html,
  releases, previews, content-locks.json, or the public site in this phase.
- Do not push/publish or delete the original project. Prepare an exact checkpoint
  and obtain the separately required remote-write authorization first.
- Do not commit other work from the original project; it has local-only files.
- Do not run legacy importers, including --check or internal functions:
  bandsheet_import.py, import_edited_song_html.py, busk_import.py, _work/busk-import.html.
- Some legacy tests execute suspended importers. Do not blindly run all tests;
  use the synthetic suite below. Do not weaken policy to get tests green.
- Never fetch or invent chords/lyrics, normalize musical data, or create approval
  from baseline equality, test results, Git status, or a filename/version badge.

## Sole authority and obsolete material

This file replaces the previous 411-line AGENTS.md as active governance. Old
workflow instructions, plans, archived documents and inline HTML prompts are
obsolete as operational instructions. Their exact history remains in Git.
architecture/*.md describes technical contracts/evidence, not separate AI policy.

Obsolete does not mean safe to delete immediately. Existing song HTML remains the
canonical disk source during transition; obsolete code must not imply obsolete
musical data. Frozen releases are historical evidence and must not be rewritten.
Legacy guards remain transitional protection until replacement coverage exists.
See architecture/retirement-plan.json for dependencies and deletion gates.

Use hard-task-metacognition and ti-vault-hard-task-adapter for cross-file work.
The shared vault rules remain applicable: right-ai-tool-escalation-rule.md,
cost-aware-model-routing-rule.md, ti-style-value-density-principle.md under
/Users/ti_am1/vaults/00-vault-system/ai-working/.
Before new UI design, read the shared apps DESIGN_PHILOSOPHY.md and design/.
Keep the Luminous rehearsal-first design; no unrelated redesign.

## Target source of truth

One remote Git repository is the durable authority. Local clones, browser state,
Downloads, _work and local revision stores are working/recovery caches only.
Draft branches are not canonical selection and must not deploy to the public site.

Target roles after explicit cutover:
- song-revisions/<songId>/<revisionHash>.json: immutable full revision objects.
- song-data/<songId>.json: selected revision pointer; no second full payload copy.
- band/playlist relationship sources: stable IDs, complete order/notes preserved.
- catalog: derived projection; never edits song revisions.
- editor/index/build source: separately versioned and hashed.
- approvals: exact revision decisions with external authority evidence, not a
  self-authenticating JSON flag. AI technical review and Ti musical approval differ.
- release manifest: exact inputs/artifacts/evidence; not permission to publish.

Until cutover, songs/*.html, relationship JSON, templates and locks retain their
previous roles. Browser exports may be newer than disk. Preserve competing sources
and resolve provenance; Git clean cannot close that gap.

## Save contract

- Distinguish dirty, local recovery, local commit/pending remote, and verified remote.
- Only verified remote commit ancestry plus receipt/revision read-back can acknowledge
  a Git Save. Download requests and local commits cannot.
- Preserve full metadata/sections/footer/settings/extensions/provenance. Unknown
  fields are protected; unsupported schemas stop instead of dropping fields.
- Stable songId, parent revision hash, idempotent saveId and compare-and-swap updates.
- No-change/duplicate Save does not create another content revision.
- Stale parents/conflicts preserve both drafts; no silent musical merge.
- UI/render/defaults must not mutate source payload. View state is separate.
- Hashes detect drift against trusted evidence; they do not establish user approval.

The current implementation is a synthetic lab only. It intentionally rejects real
song IDs, normal project repositories and network Git remotes. A verified-test-remote
receipt is NOT GitHub durability, production readiness or approval.

## Phase gates

0. Inventory/recovery checkpoint: resolve local-only files before deletion; obtain
   separate authorization for the reviewed checkpoint push. No bulk add -A.
1. Contracts: identity, losslessness, canonicalization, Save states, conflict,
   authority and rollback documented and tested with synthetic fixtures.
2. Synthetic persistence: browser Save and Git transaction/crash/retry/tamper tests.
3. Recovery: fresh clone from the actual authorized remote, including source,
   dependencies, drafts and history; no original worktree/Downloads/_work dependency.
4. Hysteria pilot ONLY after gates above and explicit continuation scope: exact
   source SHA-256 3418e810eafe653418e5e00e92e8d23014d950b55bdf0960abb7174a0cdd1212.
   Its mixed v6.19 HTML is read-only source evidence; create a review copy only.
5. AI completes technical checks; Ti checks musical content and approves exact
   irreversible scope. Canonical replacement and publication remain separate gates.
6. Remove obsolete active files only after dependency and remote recovery gates;
   use Git history rather than multiplying archives. Never rewrite/purge history.

Dee Gern Pai / Parkhaus lyrics incident remains unresolved. Do not fill missing
lyrics, create an approval from baseline, or infer the public site's current state.

## Verification and reporting

Read-only production checks (no regeneration, report flag, lock or allowlist):

    python3 -B content_guard.py
    python3 -B validate_bandsheet.py

Synthetic checks (write only disposable test repositories/caches):

    python3 -B -m unittest discover -s tests -p 'test_song*.py'
    python3 -B -m unittest discover -s tests -p 'test_revision_integrity.py'
    python3 -B -m unittest discover -s tests -p 'test_git_revision_store.py'
    node tests/browser_revision_save.mjs

Browser tests require Node 22+ and a Chromium binary (CHROME_BIN override), and use
loopback networking plus a disposable browser profile. No user profile/credentials.
Never run update_index.py, dry-run.sh, validate.sh, push.sh or sync-latest.sh as
read-only checks: they generate, stage, rebase or publish.

Report exact scope, tool/input hashes, failures, browser/platform and omissions.
Do not use test counts as evidence of musical accuracy or whole-project recovery.
