# Review dates in Thai time

The review sheet and index show the revision number and Last edited. Approved
revisions also show Approved on. The builder projects the same timestamps into
the sheet and catalog. Both pages display exact instants in ICT (UTC+7).

New edits record the browser's edit time in UTC in the revision provenance.
Saving later preserves that edit time. A historical date with no exact time is
displayed as recorded, with “time unavailable”. An unchanged save preserves the
existing revision and its timestamps.

Build a local bundle with `build.py --review-html INPUT --output-dir NEW_FOLDER`.
The approval decision arguments match rc.6. Run `build.py --check` to verify the
template and `build.py --verify SONG` to validate a generated sheet. Use the
trusted decision arguments when verifying an approved sheet.
