# R10: Android background model of the vendor app

Kind: static. Time box: 1.5 h. You own: `results/R10.md`.

## Why
The app shell must stay connected and forward notifications in the background. Learn what the vendor app declares and relies on.

## Steps
1. `dexgrep.py $APK manifest`: list permissions, services (foreground type), receivers (boot, Bluetooth state, phone state, time change), notification listener, companion-device usage.
2. For the main BLE service: how it starts, foreground notification, restart on kill (`START_STICKY`), battery-optimisation prompts.
3. Note any permission the open client should NOT copy (location beyond what BLE scanning needs, contacts, SMS, call logs, network for analytics/ads) and why.

## Output
Answers table; "manifest for our app shell" (permissions and components with one-line reasons); "do not copy" list.

## Done when
Every permission and component in the vendor manifest is classified keep/replace/drop.
