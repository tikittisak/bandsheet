# Architecture checkpoint — 2026-11-07

Worktree: /Users/ti_am1/.codex/worktrees/bandsheet-json-architecture/bandsheet
Branch: architecture/song-data-v1. Parent draft: 3b1af0ac8aad928ab7739a9806ff2d4dccd5e704.
Authority: AGENTS.md. This handoff records facts, not additional approval.

## Implemented and verified

- Revised full-revision/hash/catalog/release contracts and active governance.
- Synthetic-only bare Git writer with atomic commits, parent checking, idempotent
  receipts, remote read-back, retry and conflict handling. Network remotes disabled.
- Derived Luminous adapter with complete revision envelope, protected unknown fields,
  no startup font/render-rowSizes mutation, per-page recovery, and fail-closed legacy
  Save/template export. Existing frozen templates and song HTML remain unchanged.
- 27 synthetic unit/integration tests pass, including actual process exits at five
  Git transaction boundaries and recovery from a separate bare test remote after
  deleting the writer clone. The 18 contract/render integrity tests were repeated
  after disabling the fallback legacy Save implementation.
- Real headless Chromium 156: metadata/chord/lyric input, no-change, duplicate Save,
  reopen, unavailable remote/retry, stale-tab conflict, renderer crash recovery,
  tampered parent and missing token checks. See browser.json for exact scope.
- Production guard and validator pass for 72 songs, approved locks=0. Protected file
  hashes are recorded for 100 files. No musical correctness claim follows.

## Gates still closed

- No GitHub push, public change, canonical migration, content lock or real-song pilot.
- Local test-remote results do not prove network transport or actual GitHub recovery.
- Full-project clean clone/build recovery has not been completed.
- Original project has 2 untracked and 707 ignored files. Their provenance has not
  been reconciled. No matching HTML was found at Downloads root; this is not proof
  that no newer browser exports exist elsewhere. Do not delete either project.
- Nothing obsolete was deleted yet: remote checkpoint and dependency gates remain.
- Existing full test suite was not run because it invokes suspended legacy importers.
- Actual remote integration, deployment isolation, approval authority, promotion and
  rollback remain work to implement/review. Safari/mobile/physical power-loss absent.
- Dee Gern Pai lyrics incident remains unresolved. Hysteria remains read-only and
  its pilot requires the exact SHA and gates in AGENTS.md.

## Next bounded step

Review this checkpoint and the remote's deployment configuration read-only. Prepare
an exact branch-only push for separate authorization; never run push.sh (it targets
main and generates/stages broadly). Resolve original-project local-only provenance
before retirement. After authorized checkpoint push, clone independently from that
actual remote and verify source/dependencies/fixtures/history without relying on
local common .git or ignored files. Open the pilot gate only after recovery passes.

Evidence: verification/2026-11-06-architecture/{summary.json,inventory.json,
unit-tests.txt,browser.json}. Schema/hash details: architecture/song-data-v1.md.
