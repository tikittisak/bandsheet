# Hysteria rc.7 review checkpoint

This is a local pilot for Hysteria, built from `architecture/song-data-v1` at
`db2df1782f4b3fce36b52fbff75613f8633fc17a` plus the review code in this
checkpoint. The canonical source is `songs/hysteria.html` at that baseline,
SHA-256 `3418e810eafe653418e5e00e92e8d23014d950b55bdf0960abb7174a0cdd1212`.

The three HTML files in this evidence directory are exact snapshots of browser
exports. Their payloads contain Hysteria's review data.

| Revision | File | Revision SHA-256 | File SHA-256 |
| --- | --- | --- | --- |
| r2 | `hysteria-rc5-r2.html` | `d88e194bf9a603491344d538cfdeed931e9483a7a9015386f231bb1bdaa9e307` | `3494ed228087330350698eb496891353a6a5e100f3ade0f94cc6a368e2cfd429` |
| r3 | `hysteria-rc7-r3.html` | `b0bc3c2b63d287e86309a97670a8ec84da352ca4791fedda8ea90fb32ef69819` | `efccf759c32e932c05b6f09802f39f522993c0071b059f62aff644120a097312` |
| r4 | `hysteria-rc7-r4.html` | `90eeeb7642ee207a40cb703ea38d53a8c9c46ea951f7e9d215ecb432481d19bd` | `511e54735a6dbca30da5be301c43adeb0b09569e3b528b6ae1005a052b6c4956` |

Ti explicitly approved the attached r4 in Codex chat
`01a1b4d0-5fdd-7472-aab4-76a8489b7bbb`. The decision records the local
clock time sampled on receipt. Ti later confirmed in the same chat that the
sheet and index matched. The earlier automated display check used Node
with a minimal DOM stub. Its result and the generated bundle hashes are
recorded in `verification.json`. The approved review scope is Hysteria r4.

Run from the repository root to reconstruct the review in a temporary folder.

```sh
evidence=verification/2026-11-07-hysteria-rc7-r4
builder=src/sheet/templates/luminous-v7.0.0-rc.7-review/build.py
decision_sha=cc40313037525348b3f1f57176fd8cc8716101065d150e33991f05fc8cd4777c
review_dir=$(mktemp -d)
cp "$evidence/hysteria-rc7-r4.html" "$evidence/decision.json" "$review_dir/"
python3 -B "$builder" --output-dir "$review_dir/review" \
  --review-html "$review_dir/hysteria-rc7-r4.html" \
  --decision "$review_dir/decision.json" --decision-sha256 "$decision_sha"
python3 -B "$builder" --verify "$review_dir/review/song.html" \
  --decision "$review_dir/decision.json" --decision-sha256 "$decision_sha"
node "$evidence/verify-display.mjs" "$review_dir"
```

Open the generated `review/index.html` and follow Hysteria. Both pages display
`Approved · r4` and `Approved on: 7 Nov 2026, 14:20 ICT`.
