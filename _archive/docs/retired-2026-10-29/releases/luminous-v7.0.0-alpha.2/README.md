# Retired document — 2026-10-29

Original path: `releases/luminous-v7.0.0-alpha.2/README.md`
Role: historical/reference snapshot, NOT current operating instructions.
Replacement: repository-root `AGENTS.md` is the sole project workflow authority.
Snapshot includes local uncommitted edits present at retirement; this is not a release approval.

---

# Luminous v7.0.0-alpha.2 — hardened manual trial

Date: 2026-10-29. Source UI reference: `4fb98e9` (alpha.1).

Start with `_archive/prototypes/luminous-v7.0.0-alpha.2-blank.html`.
Click edit, enter song metadata/chords/lyrics manually, then save html.
Open the downloaded HTML and verify the saved changes. Export is a local file;
it does not update GitHub. Keep the saved file as the manual draft. Legacy
importers are suspended; do not import this file through them.

Rebuild both blank template and Resistance trial preview:

```bash
python3 -B tools/build_luminous.py
python3 -B -m unittest discover -s tests
python3 -B content_guard.py
python3 -B validate_bandsheet.py
```

Changes:

- Browser Save HTML escapes inline JSON script terminators and user title text.
- UI typography no longer writes into SETTINGS on startup.
- Content guard includes SETTINGS and detects executable script/handler changes
  separately from data changes. Raw inline script terminators are rejected.
- Existing approval records cannot disappear or be rewritten silently relative
  to HEAD. No real approval records were created or refreshed.
- Legacy Python importer CLI entrypoints and browser import/export actions stop
  immediately. Their historical implementations remain for reference only.
- Push entrypoints validate before generation, after generation and check
  content again after staging. Staging failures cannot advance to commit.

Verification: 17 unit/integration tests pass, including temporary-file mutations
and both push entrypoints rejecting an invalid template. Actual browser test:
blank draft → title audit-luminous-alpha2-test / BPM 100 / C7 → export → reopen;
all three values persisted. Test export resides under `_work/audit/`.
All 72 canonical songs, production template and content-locks file were compared
byte-for-byte against 4fb98e9 and remained unchanged. No commit/push performed.

Limits: local guards do not restrict an AI with direct repository write access
from editing or bypassing the guard itself. This is not an authorization boundary
or a full security certification. Canonical v6.19 song pages have not been synced
with these new export fixes. There is no autosave, cloud sync, general Undo,
or automatic browser-export intake. New drafts require deliberate local export.
