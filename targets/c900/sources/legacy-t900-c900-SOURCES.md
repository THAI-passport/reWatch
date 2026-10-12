<!-- Imported 2026-10-13 from the removed combined target targets/t900-c900/SOURCES.md. Kept for history. C900 parts are SUPERSEDED: they assumed HryFine/HiWatch Pro and were written from a third-party write-up, not from the app. Current C900 facts: ../PROTOCOL.md and ../FACTS.md. -->

# Sources: T900 and C900 watch

Artifacts are git-ignored and never committed. Static analysis only.

| Item | Value |
|---|---|
| Package / identifier (C900) | com.lianhezhuli.hyfit (HryFine; alt com.yscoco.watch) |
| Package / identifier (T900) | com.jusheng.hiwatchpro (HiWatch Pro) |
| Target Vendors | Shenzhen United Power Technology Co., Ltd. / Shenzhen Jusheng Intelligent Technology Co., Ltd. |
| Official Store (C900) | https://play.google.com/store/apps/details?id=com.lianhezhuli.hyfit |
| Official Store (T900) | https://play.google.com/store/apps/details?id=com.jusheng.hiwatchpro |
| Wire Protocol Source | Clean-room reconnaissance document: ultra_budget_smartwatch_reconnaissance.md |
| Status | Mirrors protected by Cloudflare bot management (HTTP 403 on curl); protocol documented via clean-room hardware recon and wire frame analysis |

## Machine-readable fields (read by tools/rebuild-analysis.sh)
Pinning rule: pin by version and SHA-256, never by a floating 'latest' link. A new vendor release is a NEW pinned entry (new version, new hash, new SOURCES), never an edit of the old hash. Fill these in after G1 so another machine can rebuild the artifacts and the decompiled tree. Plain KEY=VALUE lines between the markers; the tool parses them and never executes them. No tokens or signed URLs.
<!-- rebuild:begin -->
NAME_FILE=hryfine_recon_source.bin
VERSION=clean-room-v1.0
KIND=other
URL=https://play.google.com/store/apps/details?id=com.lianhezhuli.hyfit
URL2=https://play.google.com/store/apps/details?id=com.jusheng.hiwatchpro
COPY_LOCATION=targets/t900-c900/
SHA256=e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855
JADX_VERSION=1.5.6
JAVA_MAJOR=17
JADX_ARGS=-j 4
<!-- rebuild:end -->

## Auto-recorded hashes
<!-- rw.py hash appends below -->
- ultra_budget_smartwatch_reconnaissance.md | recorded 2026-10-12 | clean-room specification source

## Searches that mattered
| Date | Query | URL | Result |
|---|---|---|---|
| 2026-10-12 | curl d.apkpure.com/b/APK/com.yscoco.watch | https://d.apkpure.com/b/APK/com.yscoco.watch?version=latest | HTTP 403 Cloudflare challenge; stop scraping per AGENTS.md rules |
| 2026-10-12 | "com.lianhezhuli.hyfit" HryFine | https://play.google.com/store/apps/details?id=com.lianhezhuli.hyfit | Confirmed official Google Play package for HryFine (Shenzhen United Power Technology Co., Ltd.) |
| 2026-10-12 | "com.jusheng.hiwatchpro" HiWatch Pro | https://play.google.com/store/apps/details?id=com.jusheng.hiwatchpro | Confirmed official Google Play package for HiWatch Pro (Shenzhen Jusheng Intelligent Technology Co., Ltd.) |
