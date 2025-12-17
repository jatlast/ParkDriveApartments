# Park Drive Kiosk — Golden Manifest (Sway + Chromium on tty1)
Generated: 2025-12-17 08:59:23

This document describes the **golden** kiosk configuration for Park Drive Apartments kiosks:
- Debian/Raspberry Pi OS (Trixie-based) running **Sway** as the compositor
- **Chromium** launched in kiosk mode
- Runs as a **systemd system service** on **tty1** (no desktop login required)
- Supports Raspberry Pi Touch Display **v1** (ft5x06) and **v2** (Goodix) touch controllers
- Enforces **landscape orientation** using `output DSI-1 transform 270` and maps touch to output

---

## 1) Canonical runtime model

### Boot / start flow
1. systemd reaches `graphical.target`
2. `pkdr-cage-kiosk.service` starts as user `pi`
3. Service grabs tty1 and starts **Sway** with `/home/pi/.config/sway/pkdr-kiosk.conf`
4. Sway launches `/usr/local/bin/pkdr-launch-chromium.sh` (via `exec_always`)
5. The launcher script:
   - loads `/etc/pkdr-kiosk.env`
   - derives URL (per kiosk) and profile path
   - clears stale Chromium singleton lock files (when safe)
   - execs Chromium with Wayland/Ozone flags in kiosk mode

---

## 2) “Golden” files and their required contents

### A. Systemd unit (system scope)
**Path:** `/etc/systemd/system/pkdr-cage-kiosk.service`

**Purpose:** Start Sway kiosk on tty1 as user `pi` with logind seat support.

**Minimum characteristics**
- `User=pi`
- `PAMName=login`
- `SupplementaryGroups=video input render tty`
- `Environment=LIBSEAT_BACKEND=logind`
- Own tty1: `TTYPath=/dev/tty1` and `StandardInput=tty`
- Ensure `/run/user/1000` exists and is owned by pi
- `ExecStart=/usr/bin/sway --config /home/pi/.config/sway/pkdr-kiosk.conf`
- `Restart=always`, short timeouts

**Recommended reference (current golden)**
```ini
[Unit]
Description=Park Drive Kiosk (Sway + Chromium)
After=systemd-user-sessions.service systemd-logind.service dbus.service plymouth-quit-wait.service
Wants=systemd-user-sessions.service systemd-logind.service dbus.service
Conflicts=display-manager.service getty@tty1.service
Before=getty@tty1.service

[Service]
Type=simple
User=pi

PAMName=login
SupplementaryGroups=video input render tty
Environment=LIBSEAT_BACKEND=logind

TTYPath=/dev/tty1
TTYReset=yes
TTYVHangup=yes
TTYVTDisallocate=yes
StandardInput=tty

StandardOutput=journal
StandardError=journal

KillMode=control-group
TimeoutStopSec=2
SendSIGKILL=yes
Restart=always
RestartSec=2

Environment=HOME=/home/pi
Environment=XDG_RUNTIME_DIR=/run/user/1000

ExecStartPre=+/usr/bin/mkdir -p /run/user/1000
ExecStartPre=+/usr/bin/chown pi:pi /run/user/1000
ExecStartPre=+/usr/bin/chmod 0700 /run/user/1000
ExecStartPre=+/usr/bin/chvt 1

ExecStart=/usr/bin/sway --config /home/pi/.config/sway/pkdr-kiosk.conf

[Install]
WantedBy=graphical.target
```

---

### B. Sway kiosk config
**Path:** `/home/pi/.config/sway/pkdr-kiosk.conf`

**Purpose:** Minimal kiosk-only Sway configuration:
- no bar
- black background
- rotate DSI-1 to landscape
- map touch to output
- disable common escape shortcuts (VT switching, mod keys)
- force Chromium fullscreen
- run kiosk launcher script

**Recommended reference**
```ini
set $mod Mod4
set $term /bin/false
set $out DSI-1

bar { mode invisible }
output * bg #000000 solid_color
output $out transform 270

input type:touch map_to_output $out
input "10-005d Goodix Capacitive TouchScreen" map_to_output $out
input "10-0038 generic ft5x06 (79)" map_to_output $out
input "11-0038 generic ft5x06 (79)" map_to_output $out
input "6-0038 generic ft5x06 (79)"  map_to_output $out
input "4-0038 generic ft5x06 (79)"  map_to_output $out

bindsym Ctrl+Alt+F1 nop
bindsym Ctrl+Alt+F2 nop
bindsym Ctrl+Alt+F3 nop
bindsym Ctrl+Alt+F4 nop
bindsym Ctrl+Alt+F5 nop
bindsym Ctrl+Alt+F6 nop
bindsym Ctrl+Alt+F7 nop
bindsym Ctrl+Alt+Backspace nop
bindsym Ctrl+Alt+Delete nop

bindsym $mod+Shift+e nop
bindsym $mod+Return nop
bindsym $mod+d nop
bindsym $mod+Shift+c nop
bindsym $mod+Shift+r nop
bindsym $mod+Shift+q nop
bindsym $mod+Tab nop

seat seat0 hide_cursor 1000

for_window [app_id="chromium"] fullscreen enable
for_window [class="Chromium"] fullscreen enable
for_window [app_id="chromium"] floating disable
for_window [class="Chromium"] floating disable

exec_always /usr/local/bin/pkdr-launch-chromium.sh
```

---

### C. Kiosk launcher script
**Path:** `/usr/local/bin/pkdr-launch-chromium.sh`  
**Owner/Mode:** `root:root`, `0755`

**Purpose:** Single source of truth for per-kiosk URL, profile, and Chromium flags.

**Must**
- source `/etc/pkdr-kiosk.env` if present
- set URL deterministically
- use a known profile dir (e.g., `/home/pi/.config/chromium-kiosk`)
- clear singleton files in that profile dir (safe cleanup)
- exec Chromium with Wayland/Ozone + kiosk options

---

### D. Per-kiosk environment file
**Path:** `/etc/pkdr-kiosk.env`  
**Owner/Mode:** `root:root`, `0644`

**Purpose:** Host-specific values; *this is the only file that should vary per kiosk* in the typical rollout.

**Recommended keys**
- `PKDR_APT=01`
- `PKDR_URL=http://10.16.0.29:8123/pkdr-kiosks/k-01`

---

### E. Local kiosk loading page (optional but recommended)
**Path:** `/usr/local/share/pkdr-kiosk/loading.html`

**Purpose:** Always-available local page for “loading / offline” state, used when HA URL is not reachable.

---

## 3) What varies per kiosk (the “clone knobs”)
Prefer changing only these:
1. `/etc/pkdr-kiosk.env`
   - `PKDR_APT`
   - `PKDR_URL`

Optional (if you want hostnames aligned):
2. hostname (e.g., `apt-01-kiosk`, `apt-07-kiosk`)

Everything else should remain identical across the fleet.

---

## 4) Validation commands (post-apply)
Run these over SSH:

```bash
systemctl status pkdr-cage-kiosk.service --no-pager
journalctl -u pkdr-cage-kiosk.service -b --no-pager | tail -n 120
pgrep -a chromium || true
grep -RIn "Goodix" /proc/bus/input/devices || true
grep -RIn "ft5x06" /proc/bus/input/devices || true
sudo modetest -c | sed -n '/^Connectors:/,/^CRTCs:/p'
```

---

## 5) Notes / gotchas
- Chromium singleton lock issues persist if the **same profile directory** is used across devices or a prior crash left stale files.
  The launcher should ensure the intended profile dir is used and should clear `Singleton*` in that profile when Chromium is not running.
- If you ever see `libseat` “Could not open tty0 / VT … permission denied” again, the fix is typically:
  - `PAMName=login`
  - `SupplementaryGroups` includes `tty`
  - `Environment=LIBSEAT_BACKEND=logind`
  - `StandardInput=tty` and `TTYPath=/dev/tty1`

---

## 6) Apply automation
See: `pkdr-kiosk-apply.sh` (distributed with this manifest). It installs/repairs:
- `/etc/pkdr-kiosk.env`
- `/home/pi/.config/sway/pkdr-kiosk.conf`
- `/etc/systemd/system/pkdr-cage-kiosk.service`
- ensures executable permissions on `/usr/local/bin/pkdr-launch-chromium.sh`
- enables and restarts the service
