# Fact sheet: T900 and C900 watch

Single place for values that sources disagree on. Other documents link here. Change a value here first.

Tags: [C] confirmed in artifact, [V] verified by emulation/vector, [H] hardware, [W] third-party, [I] inferred, [U] unknown.

| Topic | Value | Tag | Source | Conflicts with |
|---|---|---|---|---|
| C900 NUS UUID ending | 6E400001-...-E50E24DCCA9F | [W] | ultra_budget_smartwatch_reconnaissance.md §3.2 | Standard Nordic NUS ends in ...DCCA9E [W]; client must accept both |
| T900 / C900 Shared App | No; separate apps (HiWatch Pro vs HryFine) | [W] | ultra_budget_smartwatch_reconnaissance.md §1; Play Store | White-label marketing claiming universal cross-compatibility |
| Biometric Sensor Validity | Zero (cosmetic green LEDs + synthetic timer 72-85 bpm) | [W] | ultra_budget_smartwatch_reconnaissance.md §4.1 | Vendor marketing claiming optical PPG heart-rate / SpO2 tracking |
| Screen Resolution T900 | 240x286 TFT (common) vs 320x385 (Ultra 2 variants) | [W] | ultra_budget_smartwatch_reconnaissance.md §4.2 | Marketing claiming AMOLED 410x502 resolution |
| Screen Resolution C900 | 240x286 TFT (common) vs 320x385 (Pro Max variants) | [W] | ultra_budget_smartwatch_reconnaissance.md §4.2 | Packaging claiming Retina HD 385x420 |
| Flash Memory Size | 16 MB to 64 MB (2 MB to 8 MB SPI NOR flash) | [W] | ultra_budget_smartwatch_reconnaissance.md §2.1 | Spec sheets listing 128 MB RAM (actually 128 KB internal SRAM) |
| OTA Bootloader Safety | Permanent brick if written to (overwrites running bootloader) | [W] | ultra_budget_smartwatch_reconnaissance.md §6.1 | Assumptions that standard DFU error-checking protects flash |
| Jieli Auth Handshake | E1/SAFER+ challenge/response on 0xAE01/0xAE02 | [V] | re-jieli skill; THAI-passport/reBeamBox | Some budget watch builds disable auth and accept open RCSP [U] |
