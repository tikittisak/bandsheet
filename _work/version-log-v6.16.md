# Bandsheet v6.16 Session Log

Date: 2026-06-03
Latest pushed commit seen locally: `d6b4e0e v6.16`

## Why This Version Exists

This session focused on making Busk import practical and keeping the main bandsheet UI stable after adding imported charts with repeats, mixed row sizes, and editable generated sheets.

The user confirmed the Busk flow will be used often because busk.town has many songs and its chord/bar structure is clear. The working direction is:

1. Open importer from the root index.
2. Copy Busk text from the song page.
3. Paste into importer.
4. Parse.
5. Review/edit metadata, section labels, and lyric/note blocks.
6. Download a finished bandsheet HTML.

## Important Files

- `_template.html`: source of truth for the live bandsheet UI, now v6.16.
- `_work/busk-import.html`: Busk importer, embeds the current template so it can download full bandsheet HTML.
- `update_index.py`: adds the root index `importer` link and keeps version text aligned.
- `.nojekyll`: required so GitHub Pages can serve `_work/busk-import.html`.
- `backup/ui-v6.15-to-v6.16-20260603-083744`: backup before the v6.16 scroll/menu fix.

## Changes In This Session

### Busk Importer

- Added `download bandsheet` flow.
- Embedded `_template.html` into importer so generated HTML does not depend on fetching `_template.html` over `file://`.
- Added editable review after parse:
  - title
  - artist
  - key
  - bpm
  - time
  - vocalist
  - section labels
  - lyric/note block enable/disable
- Export now strips importer-only private fields before copy/download.
- Added JSON verification/counting expectations to reduce repeat production of bad files.

### Template/UI

- v6.12 fixed repeat badge layout and added root index importer link.
- v6.13 fixed huge bar height caused by applying horizontal flex sizing to `.bar-cell` inside vertical columns.
- v6.14 fixed row-size changes deleting bars. Reducing display count now reflows rows instead of removing bars.
- v6.15 fixed `+ bar` behavior so adding bars fills the current row up to the default row size before creating new rows.
- v6.16 fixed scroll jank when hiding menu:
  - old behavior changed `top` and `marginTop` during scroll
  - new behavior uses `transform`
  - menu heights are measured only on load/resize
  - scroll bounce at top/bottom is clamped
  - tiny scroll deltas are ignored

## Bugs/Risks To Remember

- Browser visual verification was limited because local `file://` / localhost testing was sometimes blocked by the browser environment. Static checks and script syntax checks passed.
- Files downloaded from importer should be checked by opening the HTML and comparing bar counts/section counts against importer preview before trusting a batch of generated songs.
- If a generated file looks different from GitHub live pages, compare template version badges first. A stale embedded template in `_work/busk-import.html` is the likely cause.
- `_work` is served on GitHub Pages only because `.nojekyll` exists.
- Do not sync every tiny UI experiment to all song files. Iterate on `_template.html`, then sync only after user confirms.

## Useful Checks For Next Time

Run before pushing:

```bash
bash commands/dry-run.sh
```

Quick expectations:

- root index should report 51 songs across 5 bands unless new songs were added
- `_template.html`, song files, and embedded importer template should show the same version
- no old auto-hide menu code should write `style.top` or `style.marginTop` during scroll

## User Preferences / Decisions

- User will usually push from their own terminal.
- Prefer non-technical UI wording when explaining.
- Importer should allow manual edit after parse before download.
- Busk chord data is trusted as the source; do not invent chords from the web.
- For new songs, backup before overwriting existing files.

