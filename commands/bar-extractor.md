# Bar Extractor Command

Use this command text in a new Codex thread:

```text
bar-extractor song {song-slug}
```

Expected behavior:

1. Read `bar-extractor.md`.
2. Read PNGs from `_work/bar-extractor/cases/{song-slug}/`.
3. Create `_work/bar-extractor/outputs/{song-slug}.bars.json`.
4. Validate with `_work/bar-extractor/validate_bars.py`.
5. Report total bars, section count, warnings, and output path.

Example:

```text
bar-extractor song be-with-you
```
