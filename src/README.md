# Application sources

- `sheet/` owns editor/template behavior.
- `index/` owns catalog browsing behavior.
- `build/` owns deterministic generation.

No source in this folder may read musical content from generated HTML after the JSON cutover.
