# Synthetic Git writer

`git_store.py` is deliberately restricted to fixture IDs, dedicated bare synthetic
repositories and local bare test remotes. It cannot save into the project or push
GitHub. See architecture/song-data-v1.md for transaction and authority boundaries.
Do not remove these restrictions as a convenience. Actual remote support requires
its own authorization, deployment-isolation and clean-clone recovery checkpoint.
