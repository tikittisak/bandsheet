# Song and index approval pilot

Build a local bundle from a verified Hysteria rc.5 or rc.6 HTML export.

```sh
python3 -B src/sheet/templates/luminous-v7.0.0-rc.6-review/build.py \
  --review-html /path/to/hysteria-export.html --output-dir /path/to/new-review-folder
```

Open the bundle's `index.html`. The builder writes the same revision-specific
status to `catalog.json` and to both pages. The index is a static snapshot of
the revision it links to. It updates when a new bundle is built. An edited
download opens as Draft and retains the full song revision payload.

An actual approval requires an explicit Ti decision for that revision.
Pass its JSON record as `--decision`, with `--decision-sha256` taken from the
trusted decision evidence. The record contains `decision`, `scope`, `songId`,
`revisionHash`, `approvedAt`, `approvedBy` and `evidenceRef`. For a real song
the scope is `song-review`, approver is `Ti`, and the timestamp is ISO 8601
with a time zone. A hash confirms file identity. Authority comes from the
external decision evidence. To verify a generated approved sheet, supply the
same decision and hash with `--verify`.

The synthetic fixture route accepts only synthetic revisions and decisions.
It labels approval **Approved (test)**. The disposable Chromium test accepts
the Hysteria and synthetic approval bundle directories as its two arguments.
