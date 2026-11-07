# Local review template rc.4

The lyric editor has Bold, Italic and Underline controls. Both remains the default
view. Save HTML downloads a local draft. This template inherits the local export
route from rc.3, which uses no Git writer.

The earlier review showed a Save HTML button that called the synthetic Git Save
handler. The review page had no writer, so it could not produce a file. The older
template also hid the formatting toolbar and did not build its controls. The
review renderer now requires an explicit local export template, and the browser
test exercises the controls and reads the downloaded file from disk.

The rc.3 export copied the live DOM. That included rebuilt rhythm and beat items
and could carry the viewport width or Save status into the file. rc.4 clears only
known transient containers and state from the export clone. Rhythm and beat
handlers and their existing visibility rules are preserved. The retired export
helpers were removed after checking their references in the pinned template.

Run from the worktree root:

```sh
python3 -B src/sheet/templates/luminous-v7.0.0-rc.4-review/build.py --check
node tests/browser_review_template.mjs
node tests/browser_review_template.mjs /path/to/approved-hysteria-review.json
```

The browser gate uses Chromium with a temporary profile and download directory.
It checks B/I/U, Both/Band/Vocal, the blank template, actual download and reopen,
revision and payload equality, picker behavior, and byte-stable re-export.
The optional Hysteria run requires the exact pilot revision. Re-run both cases
before changing the template used for more songs.
