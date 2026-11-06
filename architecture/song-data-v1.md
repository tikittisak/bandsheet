# Bandsheet JSON Architecture · v1 Draft

Status: architecture and synthetic round-trip checkpoint complete. No canonical migration or production promotion is authorized.

## Goal

Make song data durable and independently versioned so sheet UI, index UI, and release packaging can change without rewriting musical content.

## Source roles

| Path | Role |
|---|---|
| `song-data/*.json` | Future canonical song revisions after explicit promotion |
| `song-revisions/<song-id>/*.json` | Append-only captured browser revisions; never overwrite an earlier revision |
| `schemas/*.schema.json` | Data contracts |
| `src/sheet/` | Song editor/template source |
| `src/index/` | Index application source |
| `src/build/` | Deterministic build source |
| `songs/*.html` | Existing public paths; generated artifacts only after cutover |
| `index.html`, `<band>/index.html`, playlist HTML | Generated public artifacts only after cutover |
| `bands/*.json`, `playlists/*/*.json` | Existing relationship sources; migrate from filenames to stable `songId` only after a compatibility plan |
| `_work/` | Local temporary files; never canonical or the only copy of an accepted revision |

The existing 72 `songs/*.html` files remain immutable evidence during this phase. Their pinned Git trees are recorded in `baseline-5a5ff48.json`.

## Identity and hashes

- `songId` is immutable and is not derived again from a filename after creation.
- `slug` controls the public filename and may change only through an explicit redirect/reference migration.
- `contentRevision` increments only when metadata, sections, footer, or settings change.
- `contentHash` is SHA-256 of canonical metadata, sections, footer, and settings.
- `revisionHash` is SHA-256 of the complete song revision, including identity and provenance.
- Approval records live outside the song document and bind an exact `songId + contentHash`.
- Generated HTML has an artifact hash but never becomes the authority for content after cutover.

## Independent versions

| Field | Meaning |
|---|---|
| `schemaVersion` | Song/catalog contract compatibility |
| `contentRevision` | Per-song content history |
| `editorVersion` | Song sheet UI/editor behavior |
| `indexVersion` | Index UI/behavior |
| `catalogBuildHash` | Exact derived catalog snapshot |
| `releaseId` | A pinned combination of editor, index, catalog, generators, and public artifacts |

Changing editor or index code must not increment song content revisions. Changing song content must not change `editorVersion` or `indexVersion`.

## Build boundary

The future build reads only canonical JSON and relationship JSON, then emits self-contained HTML for offline use. Generated pages may embed a copy of the JSON, but edits to generated HTML are never promoted directly. Browser edits export a revision document with parent hash; intake stores it append-only before review or promotion.

## Current checkpoint

This phase may add contracts, synthetic fixtures, validators, and tests. It must not:

- extract or normalize the 72 real songs into canonical JSON;
- change `songs/*.html`, indexes, bands, playlists, approvals, or frozen releases;
- execute a batch transfer;
- commit or publish production replacements.

## Verified synthetic gate

The committed fixture now covers validate → derive catalog → render self-contained HTML → reopen embedded data → compare semantic payload and hashes. The renderer is deterministic, preserves the input revision, escapes metadata attributes, and prevents inline JSON from closing its script element.

This verifies the data/build boundary only. It does not certify browser editing behavior or any real song. The next gate is browser-based edit/export/reopen testing with synthetic data, followed by an explicit review decision before extracting even one real song.
