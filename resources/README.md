# resources/

Exactly pinned vendor archives that the owner explicitly allowed into git, so cloud agents can rebuild without a download. Nothing else goes here.

Rules (AGENTS.md ground rule 3):
- One zip per artifact, holding exactly one file, stored with Git LFS (`.gitattributes`).
- Each zip is listed as `REPO_COPY` with `REPO_COPY_SHA256` in a `targets/<slug>/SOURCES.md`; the inner file's hash is the target's `SHA256`. `python3 tools/rw.py lint` rejects any other file here.
- `.gitignore` allows each file by exact path. Decompiled trees, work folders and loose APK/XAPK files stay ignored.
- A new vendor release is a new zip and a new SOURCES entry, never a replacement of an existing one.

| File | Target | Approved | Zip SHA-256 |
|---|---|---|---|
| `c900/hiwear-plus-2.0.1.xapk.zip` | c900 (Hiwear Plus 2.0.1) | owner, 2026-10-13 | `800662003d57aa272e5f829908c4c7671d1118ac4ed564242a5edcd4ca8e570e` |

Fresh clone: `git lfs install && git lfs pull`, then `python3 tools/rebuild_analysis.py c900 --max-heap 3g`.
