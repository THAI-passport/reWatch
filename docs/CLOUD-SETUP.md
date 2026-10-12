# Cloud agent setup (minimal)

One-shot setup for a cloud LLM box (Claude Code cloud, Antigravity, etc.) that needs the C900 Hiwear Plus tree rebuilt. Prefer `bash tools/cloud_bootstrap.sh`. The script is idempotent and prints `PASS` or `FAIL: ...`.

Pinned tools (AGENTS.md: version + SHA-256):

| Tool | Version | Artifact | SHA-256 |
|---|---|---|---|
| jadx | 1.5.6 | `jadx-1.5.6.zip` | `545ea2be9c242511bc145755cf4bda2485ade42966e096f8b4d3da2a230e8974` |
| apktool | 3.0.3 | `apktool_3.0.3.jar` | `dbf930b076c6b9be08d57c449cacefc3bdd6b71ebd59b3066fc0e1f5b14f9423` |
| Hiwear zip | 2.0.1 | `resources/c900/hiwear-plus-2.0.1.xapk.zip` | `800662003d57aa272e5f829908c4c7671d1118ac4ed564242a5edcd4ca8e570e` |

JDK: OpenJDK 17+ (distribution not pinned; prefer `openjdk-17-jdk-headless` from apt).

## One command (preferred)

From the repo root on branch `feat/c900-hiwear-plus` (or a branch that contains the REPO_COPY):

```bash
bash tools/cloud_bootstrap.sh
```

Exit 0 and a final line `PASS` means you can start the recon task. `FAIL: ...` means stop and use the troubleshooting table.

## Copy-paste block

From the repo root (after clone + checkout of this branch):

```bash
bash tools/cloud_bootstrap.sh
# optional: JADX_HEAP=2g CLOUD_TOOLS_DIR=$HOME/tools bash tools/cloud_bootstrap.sh
```

The script is the source of truth for install steps, pinned URLs, and SHA-256 checks (jadx 1.5.6, apktool 3.0.3, the Hiwear zip). Read `tools/cloud_bootstrap.sh` if you need to run steps by hand (for example when `curl|bash` is forbidden — open the file and run each section).

## Troubleshooting

| Symptom | Cause | What to do |
|---|---|---|
| Zip is a tiny text file / starts with `version https://git-lfs.github.com` | LFS object not fetched (quota, auth, or host block) | `git lfs env`; retry `git lfs pull -I resources/c900/hiwear-plus-2.0.1.xapk.zip`; ask owner if bandwidth exhausted |
| `jadx download blocked` / curl 403 | GitHub release fetch filtered | Upload the pinned zip to the box by hand, place under `$HOME/tools/`, or ask owner for a mirror; do not skip the SHA check |
| Java install fails | No apt / no sudo | Install any JDK 17+ another way; `java -version` must show 17+ |
| jadx OOM / killed | Heap too large for the box | `JADX_HEAP=2g bash tools/cloud_bootstrap.sh` (or `1g`); close other processes |
| jadx exit 3 | Some methods failed to decompile | **Normal.** Continue; use smali (`apktool d` without `-s`) for any numeric that matters |
| `FAIL: zip SHA-256 mismatch` | Wrong/corrupt LFS object | Delete the zip, `git lfs pull -I ...` again; never `--accept-new-hash` silently |
| rebuild wants a network download | REPO_COPY missing or not declared | Confirm `targets/c900/SOURCES.md` has `REPO_COPY=resources/c900/hiwear-plus-2.0.1.xapk.zip` on this branch |

## After PASS

Open `targets/c900/tasks/RECON-HIWEAR-APK.md` and follow the starter prompt + token-saving section. Do not decompile "to explore".
