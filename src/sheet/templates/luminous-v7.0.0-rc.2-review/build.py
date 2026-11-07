#!/usr/bin/env python3
"""Reproduce the local Both-view template from the pinned Luminous rc.1."""
import argparse
import hashlib
import json
from pathlib import Path

FOLDER = Path(__file__).resolve().parent
ROOT = (FOLDER / '../../../..').resolve()

VIEW_CHANGES = (
    (
r'''  body:not(.edit-mode).view-band .section-tag { min-height: 24px; }
}
</style>
</head>
''',
r'''  body:not(.edit-mode).view-band .section-tag { min-height: 24px; }
}

/* Both follows the existing section pairs, stacking below a readable two-column width. */
body:not(.edit-mode).view-both .section-pair.no-lyric { grid-template-columns: minmax(0, 1fr); }
body:not(.edit-mode).view-both .lyric-placeholder { display: none; }
@media (max-width: 960px) {
  body:not(.edit-mode).view-both .section-pair { display: block; }
  body:not(.edit-mode).view-both .section-pair .note-type-sec .sec-note-wrap { padding-top: 0; }
  body:not(.edit-mode).view-both .section-pair .sec-note-cols { margin-left: 0; }
}
@media (max-width: 760px) {
  body:not(.edit-mode).view-both .section-tag .section-name { padding-right: 0; }
  body:not(.edit-mode).view-both:not(.toolbar-more-open) #toolbar .tb-group[aria-label="Key"],
  body:not(.edit-mode).view-both:not(.toolbar-more-open) #toolbar .tb-group[aria-label="Readability"] { display: none; }
}
</style>
</head>
''',
    ),
    (
r'''    <div class="seg-ctrl">
      <button class="seg-btn" id="band-view-btn" onclick="setPerformanceView('band')">band</button>
      <button class="seg-btn" id="vocal-view-btn" onclick="setPerformanceView('vocal')">vocal</button>
    </div>
''',
r'''    <div class="seg-ctrl">
      <button class="seg-btn" id="band-view-btn" onclick="setPerformanceView('band')">band</button>
      <button class="seg-btn" id="both-view-btn" type="button" onclick="setPerformanceView('both')" aria-label="Both: bars and lyrics">both</button>
      <button class="seg-btn" id="vocal-view-btn" onclick="setPerformanceView('vocal')">vocal</button>
    </div>
''',
    ),
    (
r'''  };

  var PERFORMANCE_VIEW = window.matchMedia('(max-width: 760px)').matches ? 'vocal' : 'band';
  window.setPerformanceView = function (mode) {
    var nextView = mode === 'vocal' ? 'vocal' : 'band';
    if (nextView !== PERFORMANCE_VIEW) closeChordPeeks();
    PERFORMANCE_VIEW = nextView;
    document.body.classList.toggle('view-band', PERFORMANCE_VIEW === 'band');
    document.body.classList.toggle('view-vocal', PERFORMANCE_VIEW === 'vocal');
    document.body.dataset.performanceView = PERFORMANCE_VIEW;
    var band = document.getElementById('band-view-btn');
    var vocal = document.getElementById('vocal-view-btn');
    if (band) band.classList.toggle('active', PERFORMANCE_VIEW === 'band');
    if (vocal) vocal.classList.toggle('active', PERFORMANCE_VIEW === 'vocal');
    requestAnimationFrame(syncPairOffsets);
  };
''',
r'''  };

  var PERFORMANCE_VIEW = 'both';
  window.setPerformanceView = function (mode) {
    var nextView = mode === 'both' || mode === 'vocal' ? mode : 'band';
    if (nextView !== PERFORMANCE_VIEW) closeChordPeeks();
    PERFORMANCE_VIEW = nextView;
    document.body.classList.toggle('view-both', PERFORMANCE_VIEW === 'both');
    document.body.classList.toggle('view-band', PERFORMANCE_VIEW === 'band');
    document.body.classList.toggle('view-vocal', PERFORMANCE_VIEW === 'vocal');
    document.body.dataset.performanceView = PERFORMANCE_VIEW;
    ['band', 'both', 'vocal'].forEach(function (view) {
      var button = document.getElementById(view + '-view-btn');
      if (!button) return;
      var active = PERFORMANCE_VIEW === view;
      button.classList.toggle('active', active);
      button.setAttribute('aria-pressed', String(active));
    });
    requestAnimationFrame(syncPairOffsets);
  };
''',
    ),
)
 
def render(root=ROOT):
    manifest = json.loads((FOLDER / 'manifest.json').read_text(encoding='utf-8'))
    source = (root / manifest['base']['path']).read_bytes()
    if hashlib.sha256(source).hexdigest() != manifest['base']['sha256']:
        raise ValueError('Frozen rc.1 base hash mismatch')
    document = source.decode('utf-8')
    for original, replacement in VIEW_CHANGES:
        if document.count(original) != 1:
            raise ValueError('Template view anchor missing or ambiguous')
        document = document.replace(original, replacement, 1)
    if document.count('7.0.0-rc.1') != 3:
        raise ValueError('Unexpected version anchors')
    document = document.replace('7.0.0-rc.1', manifest['version'])
    encoded = document.encode('utf-8')
    if hashlib.sha256(encoded).hexdigest() != manifest['templateSha256']:
        raise ValueError('Review template hash mismatch')
    return encoded


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument('--check', action='store_true')
    action.add_argument('--output', type=Path)
    args = parser.parse_args()
    generated = render()
    if args.check:
        if (FOLDER / 'template.html').read_bytes() != generated:
            raise ValueError('Local template differs from the pinned build')
        print('Review template matches the pinned build')
    else:
        with args.output.open('xb') as output:
            output.write(generated)


if __name__ == '__main__':
    main()
