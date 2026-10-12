# Sources: C900 watch

Artifacts are git-ignored and never committed. Static analysis only.

| Item | Value |
|---|---|
| Package / identifier | `com.myled.HiwearPlus` (Hiwear Plus, Shenzhen United Power Technology Co., Ltd.) [W] Play listing. Earlier assumption `com.yscoco.watch` (HryFine) superseded by the owner statement of 2026-10-13 |
| Version (name / code) | 2.0.1 / 31 (from the XAPK manifest) [C] |
| Source and URL (no tokens) | APKPure, `https://d.apkpure.com/b/XAPK/com.myled.HiwearPlus?version=latest` (floating; resolved to 2.0.1 on 2026-10-13). The redirect target is a signed CDN URL and is not recorded |
| File | `HiwearPlus-2.0.1.xapk` (base `com.myled.HiwearPlus.apk`, splits `config.arm64_v8a.apk`, `config.en.apk`, `config.mdpi.apk`) |
| Size (bytes) | 128092196 |
| SHA-256 | xapk `5fa761a4d16ae8980fc40a341264441fe042858876ce1267dab54bd5be7b8952`; base `931efc777ec58bc408e056da31f4e85af253a0fd35dafb6e901589829fe43a5a`; arm64 split `4c71b2819c5403cd8748931e6d24764b92ca518e677465820cb3469bf4ab7330` |
| Retrieved | 2026-10-13 (UTC+7) |

## Machine-readable fields (read by tools/rebuild-analysis.sh)
Pinning rule: pin by version and SHA-256, never by a floating 'latest' link. A new vendor release is a NEW pinned entry (new version, new hash, new SOURCES), never an edit of the old hash. Fill these in after G1 so another machine can rebuild the artifacts and the decompiled tree. Plain KEY=VALUE lines between the markers; the tool parses them and never executes them. No tokens or signed URLs.
<!-- rebuild:begin -->
PACKAGE=com.myled.HiwearPlus
NAME_FILE=HiwearPlus-2.0.1.xapk
VERSION=2.0.1
KIND=xapk
URL=https://d.apkpure.com/b/XAPK/com.myled.HiwearPlus?version=latest
COPY_LOCATION=owner to keep an exact copy of HiwearPlus-2.0.1.xapk (sha256 above) in their own storage; not yet done
SHA256=5fa761a4d16ae8980fc40a341264441fe042858876ce1267dab54bd5be7b8952
INNER_APK=com.myled.HiwearPlus.apk
INNER_SHA256=931efc777ec58bc408e056da31f4e85af253a0fd35dafb6e901589829fe43a5a
ABI_APK=config.arm64_v8a.apk
ABI_SHA256=4c71b2819c5403cd8748931e6d24764b92ca518e677465820cb3469bf4ab7330
JADX_VERSION=1.5.6
JAVA_MAJOR=17
JADX_ARGS=-j 2
<!-- rebuild:end -->

## Auto-recorded hashes
<!-- rw.py hash appends below -->

## Searches that mattered
| Date | Query | URL | Result |
|---|---|---|---|
| 2026-10-13 | "Hiwear Plus" app smartwatch Google Play package | play.google.com/store/apps/details?id=com.myled.HiwearPlus | chosen: developer Shenzhen United Power Technology; listing names M8 Pro, BZ01-116; C900 Ultra2/Ultra3 retail pages name "Hiwear Plus" as the app [W] |
| 2026-10-13 | same | uptodown (hiwear-plus.cn.uptodown.com) | same package, versions 1.0.12 to 2.0.1 listed [W] |
| 2026-10-13 | "Hiwear" app, other packages | m.hncj.com, paopaoche.net | rejected: `com.hiwear.beta` (HiWear watch-face community store) and `com.hiwear.watchclient` (an app that runs on Android watches); not companion apps for the C900 [W] |
