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

## Patch Notes After First Push

- Auto-scroll now removes toolbar/metabar from layout during play before measuring page height, matching the footer exclusion behavior.
- Speed can now be adjusted from the floating play HUD while auto-scroll is running.
- Changing speed during play recalculates the remaining scroll duration from the current position.
- The floating play HUD now uses compact `‹ x ›` controls: previous section, stop, and next section.
- Section jump skips lyric/note blocks and keeps auto-scroll playing after recalculating from the new position.

## Session Close

Closed: 2026-06-04

Final pushed commits:

- `7ee9874` — v6.17: add auto scroll and mini edit controls
- `418bd86` — v6.17: refine auto scroll measurement and speed controls
- `0999c21` — v6.17: add auto scroll section jump controls

Final state:

- Root and band indexes rebuilt successfully: 52 songs across 4 bands.
- `_template.html`, 52 published song files, and Busk importer embedded template are synced to v6.17 behavior.
- Stay With Me keeps `autoScrollDuration: "5:12"` as the real-data prototype value.
- Working tree was clean after the final push.
