# Bandsheet v6.17 Session Log

Date: 2026-06-04

## Why This Version Exists

This release adds display-mode auto-scroll and improves edit-mode mini bar controls so they are easier to tap during rehearsal prep.

## Changes

- Added auto-scroll controls to the sheet toolbar:
  - play / pause
  - song duration input
  - speed adjustment from 50% to 160%
- Auto-scroll uses the song duration and total page height rather than bar-by-bar calculation.
- Auto-scroll switches to display mode, hides toolbar/metabar while running, and hides the footer from scroll measurement.
- Manual wheel, touch, or key input pauses auto-scroll.
- Added `autoScrollDuration` and `autoScrollSpeed` to default settings and import output.
- Busk importer now reads `Duration:` when present and lets the user enter duration manually when absent.
- Mini edit controls changed from icon/square controls to text controls:
  - `@` highlight
  - `#` skip bar count
  - `%` rhythm toggle
- Fixed control/chord overlap in edit + mini mode by giving chord and controls separate real layout space instead of relying on visual transform.
- Root index importer link now carries the active band shortcut.
- Removed the obsolete `90Alter` band from index generation.

## Risk Notes

- Auto-scroll is intentionally simple and duration-based. Users can correct speed manually per song.
- The edit mini bar fix is scoped to edit + mini mode to avoid changing display layout.
- Existing song data is preserved during sync; only the template shell is updated.

## Checks

Run before push:

```bash
bash commands/dry-run.sh
```
