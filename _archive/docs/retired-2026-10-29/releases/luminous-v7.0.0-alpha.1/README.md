# Retired document — 2026-10-29

Original path: `releases/luminous-v7.0.0-alpha.1/README.md`
Role: historical/reference snapshot, NOT current operating instructions.
Replacement: repository-root `AGENTS.md` is the sole project workflow authority.
Snapshot includes local uncommitted edits present at retirement; this is not a release approval.

---

# Bandsheet Luminous v7.0.0-alpha.1

Frozen UI baseline recorded 2026-10-29 at Ti's request, from commit
`4fb98e91389ddc021dea13996d9a72a7ed11ae75`.

The exact reference is that commit's
`_archive/prototypes/preview-resistance-luminous-mobile-test.html`, verified by
SHA-256 in `manifest.json`. Git stores the reference; no duplicate song HTML was
created. A later working-tree preview is not automatically this release.

This version names the new UI direction only. The preview includes Resistance
data and is not yet a blank reusable template. Its embedded templateVersion is
still v6.19; it was intentionally not rewritten. Production `_template.html`
remains v6.19. No canonical music data was approved or changed by this freeze.

## Protection boundaries

- Legacy importers are suspended until Ti explicitly changes that decision.
- Preserve the pinned reference; subsequent UI work needs its own revision.
- No song migration or template sync is authorized by this release record.
- The manifest detects drift when verified; it is not access control, a signed
  approval, or a technical barrier against an agent that can edit these files.
- Known audit gaps remain open. This snapshot is not security certification.
  See `_work/audit/2026-10-29-integrity-audit.md` (local ignored audit evidence).

## Verify without modifying files

```bash
git show 4fb98e91389ddc021dea13996d9a72a7ed11ae75:_archive/prototypes/preview-resistance-luminous-mobile-test.html | shasum -a 256
```

Expected SHA-256:
`b5f41bda0c5cc8c87b04a0bc322559ae5b84ce27041e800a201eefb449584bc5`.

This record has not been committed or pushed by the naming/freezing task.
