# Canonical selection pointers

After an explicitly approved cutover, `<songId>.json` selects an exact immutable
revision object from song-revisions. It must not duplicate the full editable payload.
This directory currently contains no selected songs. Existing songs/*.html remain
canonical disk sources during transition. Synthetic draft pointers exist only in
disposable lab Git repositories and are never production selections.
