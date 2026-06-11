# iReal Pro Form Reference

Use this when translating an iReal Pro chart into a bandsheet bar map or chord map.

Source note: summarized from the official iReal Pro tutorial "How the Coda symbol works in iReal Pro" and verified against user-provided iReal Pro charts. Do not copy source names into final song sheets unless the user asks.

## Core Rule

The drum/score bar map in the target bandsheet remains the source of truth for bar count. iReal Pro symbols explain playback order and form, not permission to resize bandsheet sections.

## Coda Has Two Meanings

### 1. Coda As Outro Or Tag

A Coda section at the end can mean an outro/tag that plays only once at the very end.

Behavior:
- Main form repeats as configured.
- On the last pass, playback jumps or continues to the Coda ending.
- If there is only a Coda section at the end and no mid-song Coda symbol, treat it as an end tag/outro.

Bandsheet handling:
- Keep the main drum-map sections intact.
- Put the Coda material into `Outro`, `Tag`, or final `Fade Out` section.
- Do not duplicate the Coda after every chorus unless the chart explicitly makes it part of the form.

### 2. Coda As Part Of The Form

A Coda can be part of every repeat only when it is used with a text instruction such as:
- `D.S. al Coda`
- `D.C. al Coda`

Behavior:
- Play through the form until the D.S./D.C. instruction.
- Jump back to the sign (`D.S.`) or beginning (`D.C.`).
- On the appropriate pass, jump from the Coda mark to the Coda section.
- With repeats set to 1, both Coda styles can appear to behave the same: the Coda plays once near the end.

Bandsheet handling:
- Mark the repeated section in notes if needed.
- Do not flatten the playback path blindly into duplicated bars unless the user asks for a performance-linear sheet.
- For rehearsal sheets, prefer keeping the drum-map section order and adding concise notes such as `D.S. al Coda flow: return to Solo, then jump to Outro`.

## Placement Convention

Official convention:
- The `jump from` Coda symbol goes at the end of the measure.
- The `jump to` Coda symbol goes at the beginning of the first measure of the Coda section.

Bandsheet interpretation:
- If the symbol is at the end of a bar, that bar still belongs to the current section.
- The destination bar is the first bar of the Coda/Outro section.

## D.S. / D.C. Quick Reference

- `D.S.` means go back to the sign.
- `D.C.` means go back to the beginning.
- `al Coda` means continue from that return point until the Coda jump mark, then jump to the Coda section.
- `D.S. al Coda` commonly makes a chart read non-linearly; never infer extra bars from it without checking the drum/score map.

## Split Bar Rule

Use the existing split-bar syntax when one drum-map bar contains multiple harmonic events.

Examples:
- Half-bar change: `G | Em`
- Three-part compressed link inside one fixed bar: `A | C G | D`

Use split bars instead of writing `G Em` as plain text, because the rendered bandsheet shows timing more clearly.

## Comfortably Numb Notes

The iReal Pro chart shows the Link as:

```text
A | C G | D
```

For bandsheet mapping:
- If three drum-map bars are available, write: `A`, `C | G`, `D`.
- If only one fixed drum-map bar is available, write: `A | C G | D` and note that the link is compressed into one fixed bar.
- For `G Em` in verse/solo cycles, write `G | Em`.

## Final Song Sheet Hygiene

Final song HTML should not mention external website/source names in visible notes unless the user explicitly asks. Keep source and method notes in project references or `_work/`.
