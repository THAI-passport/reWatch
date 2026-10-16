# R04: Notification push rules (types, text, calls)

Kind: static. Time box: 2 h. You own: `results/R04.md`.

## Why
Notification forwarding is the main daily feature. Known: cmd 2 key 18 payload `type, 0, 0, UTF-8 "title:body"` cut at 196 bytes; type tables in C900-Q04 section 5; feature b15 0x02 (new table) is set on this watch [H]. Unknown: Android-to-type mapping, title/body handling, non-Latin text, de-dup, call push (cmd 2 key 17).

## Steps
1. Find the notification listener: `dexgrep.py $APK manifest`, then `methods` on that class; dump `onNotificationPosted`.
2. Record package-to-type mapping (public app ids are fine), title/body extraction, separator, truncation (bytes or chars), filters (ongoing, group summary), de-dup.
3. Call push: find the phone-state receiver; describe the key 17 fields and states. Never record a real number or name.
4. Which table applies with b15 0x02 set vs clear.

## Output
Answers table; "type table for this watch"; "text rules" for the core.

## Done when
Type mapping, text rules and call payload each have evidence or `[U]`.
