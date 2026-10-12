# Recording a Bluetooth log of the Hiwear Plus app on Android (owner guide)

This is optional. It lets you record what the Hiwear Plus app and your watch say to each other over Bluetooth on your own phone, so we can check our reading of the app's code without connecting anything of ours to the watch. It is linked from C900-Q13 and step HW-1 in `targets/c900/`. Plan for about 20 minutes. You do not need root.

## Before you start: privacy
- The log records **all** Bluetooth traffic on the phone while it is on: earbuds, car, other watches, and **the text of notifications** that the phone forwards to the watch.
- During the capture, send only a **test message** you are happy to share, for example "test 123" from a second phone or your own email address. Turn off other Bluetooth devices if you can.
- A bug report (step 3) also contains general phone logs. Treat the whole zip as private.
- **Never commit the raw log or bug report to git.** Share it with us privately (direct file transfer, not a public link), or keep it in the repo's `captures/` folder, which git ignores.

## 1. Turn the log on
1. Open **Settings > About phone** and tap **Build number** seven times until it says you are a developer. (Xiaomi: Settings > About phone > tap **MIUI / HyperOS version**. Samsung: Settings > About phone > Software information > Build number.)
2. Open **Settings > System > Developer options** (Samsung: at the bottom of Settings; Xiaomi: Settings > Additional settings > Developer options).
3. Turn on **Enable Bluetooth HCI snoop log**. If it offers a choice, pick **Enabled** (full), not "Filtered".
4. **Turn Bluetooth off, then on again.** Logging only starts after this restart.

## 2. Record the session (do these, in order)
1. If the watch is already bound to the app, keep it as it is; if it is new, do a **fresh pair/bind** in the Hiwear Plus app (watch on its pairing screen, add device in the app, accept any prompt). Note whether the phone asks you to "pair" in a system pop-up.
2. Let the app **sync the time** (it happens on connect; or pull down to refresh).
3. Send **one test notification** (see the privacy note) and check it shows on the watch.
4. Use **Find watch** in the app once.
5. Look at the **battery** level in the app.
6. Write down the phone time when you did each step (a rough note is fine).

**Do not** do any of these while logging: change or download a **watch face**, **OTA / firmware update**, any "upgrade" button, **unbind / remove device**, or **factory reset**. If the app offers an update, decline it.

## 3. Get the log out (no root): bug report
1. Turn **Bluetooth off** (this flushes the log to storage).
2. Either:
   - **On the phone:** Developer options > **Take bug report** > Full / Interactive. Wait a few minutes for a notification, then share the zip to yourself privately; or
   - **With a computer:** enable **USB debugging** in Developer options, connect USB, allow the prompt, then run `adb bugreport hiwear-capture.zip` (Android 7+).
3. Unzip it. The log is usually at **`FS/data/misc/bluetooth/logs/btsnoop_hci.log`**. Older or vendor builds may use `FS/data/log/bt/btsnoop_hci.log`, or a `btsnoop_hci.log` in internal storage. If there are `.last` or numbered files, keep them too.
4. Turn **Enable Bluetooth HCI snoop log** off again when done.

Brand notes:
- **Pixel / stock Android / Motorola / Nokia:** the steps above work as written.
- **Samsung:** the bug report works. Some models also keep the log under `/data/log/bt/`, which is reachable only through the bug report.
- **Xiaomi / Redmi / POCO:** you may need to sign in to a Mi account to enable USB debugging. If the bug report lacks the file, dialing `*#*#284#*#*` makes a full report zip in internal storage under `MIUI/debug_log`.
- **OnePlus / OPPO / realme / vivo:** some builds hide the log toggle or write the file only after the Bluetooth restart in step 1.4. If no file appears, tell us the model and Android version rather than trying workarounds.

## 4. Hand-off
Put `btsnoop_hci.log` in `captures/` (git-ignored) or send it privately, with your step-time notes and the phone model. We parse it with `python tools/btcap.py captures/btsnoop_hci.log` (lists writes, notifications and reads per characteristic) or Wireshark/tshark (`tshark -r btsnoop_hci.log -Y btatt`). The results are written up with the MAC address masked, and notification text is never copied into the repo.
