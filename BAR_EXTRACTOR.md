# Bar Extractor Workflow

Use this when the user says:

- `bar-extractor song {slug}`
- `extract bars song {slug}`
- `อ่าน bar จาก PNG เพลง {slug}`
- `PNG -> Song info + Bar`

Goal: inspect score PNGs and produce stable **Song info + Bar JSON**.

This workflow is Codex-assisted for now. Do not pretend there is automatic OCR/API unless it has been explicitly added and tested.

## Folder Layout

```text
_work/bar-extractor/
├── cases/{song-slug}/          # PNG inputs
├── outputs/{song-slug}.bars.json
├── prompt.md
├── schema.json
└── validate_bars.py
```

## Required Output

Save one JSON file:

```text
_work/bar-extractor/outputs/{song-slug}.bars.json
```

The JSON must contain:

- `song`: title, artist, key, bpm, time, duration when visible/known
- `sourceImages`: PNG paths used
- `bars.total`
- `bars.sections`: label/start/end/confidence/evidence
- `bars.timeChanges`: bar/time/confidence/evidence
- `warnings`: ambiguity, missing metadata, cropped pages, uncertain final bars

## Procedure

1. Locate PNGs in `_work/bar-extractor/cases/{song-slug}/`.
2. If no PNGs exist there, ask the user to put files there or identify source files.
3. Inspect images visually.
4. Extract only section names, bar ranges, total bars, and visible time-signature changes.
5. Save JSON matching `_work/bar-extractor/schema.json`.
6. Run:

```bash
python3 _work/bar-extractor/validate_bars.py _work/bar-extractor/outputs/{song-slug}.bars.json
```

7. Report output path, total bars, section count, warnings, and validation result.

## Important Rules

- Do not extract chords or lyrics in this workflow.
- Do not modify existing song HTML unless the user explicitly asks.
- Do not use web chord data.
- If a section is ambiguous, keep the best guess but add confidence and warning.
- If screenshots appear to be from a different arrangement/version, say so clearly.
