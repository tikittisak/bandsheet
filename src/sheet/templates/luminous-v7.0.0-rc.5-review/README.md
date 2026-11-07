# Local review template rc.5

The checked template is the UI shell for blank sheets and review songs. The
builder can replace only the contents of the single `bandsheet-review-data`
JSON script. The shell fingerprint covers every byte outside that slot. The
slot carries either a blank/local draft or a full revision with its metadata.
Review songs do not carry a second copy of their sections in executable code.

At startup the page captures its static markup before running the editor
scripts. Save HTML checks that shell's SHA-256 against the build's pin and
replaces only the JSON slot. Viewport sizing, active buttons, generated picker
DOM and Save status stay out of downloads. If a browser serializes the shell
differently, Save stops instead of emitting a different shell. The standalone
verifier checks the actual bytes against the pinned template in the worktree,
then validates the data slot and revision hashes.

Run from the worktree root:

```sh
python3 -B src/sheet/templates/luminous-v7.0.0-rc.5-review/build.py --check
node tests/browser_review_shell.mjs
node tests/browser_review_shell.mjs /path/to/exact-hysteria-review.json
python3 -B src/sheet/templates/luminous-v7.0.0-rc.5-review/build.py --verify /path/to/review.html
```

Use `--song-json /path/to/revision.json --output /path/to/new.html` on the same
builder to produce a review copy. It validates the revision and refuses to
overwrite a file. The browser test uses a disposable Chromium profile and
checks actual downloads, B/I/U, Both/Band/Vocal, blank-template behavior,
byte-stable re-export and rejection of a changed shell. Run it on the exact
template revision before extending review. Check each output against its own
source payload when preparing additional songs.
