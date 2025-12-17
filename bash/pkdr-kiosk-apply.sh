#!/usr/bin/env bash
set -Eeuo pipefail

# pkdr-kiosk-apply.sh
# Apply/repair the Park Drive "golden" kiosk configuration on a target Pi.
#
# Usage examples:
#   sudo ./pkdr-kiosk-apply.sh --apt 01 --url "http://10.16.0.29:8123/pkdr-kiosks/k-01"
#   sudo ./pkdr-kiosk-apply.sh --apt 07 --url "http://10.16.0.29:8123/pkdr-kiosks/k-07" --hostname apt-07-kiosk
#
# Notes:
# - This script is intentionally idempotent: safe to re-run.
# - It versions existing files before overwriting (timestamp suffix).
# - It does not require a desktop session; it manages systemd + sway kiosk.

ts() { date +"%Y%m%d_%H%M%S"; }
log() { echo "[$(date +"%F %T")] $*"; }
die() { echo "ERROR: $*" >&2; exit 1; }

require_root() {
  [[ "${EUID}" -eq 0 ]] || die "Run as root (sudo)."
}

APT_ID=""
PKDR_URL=""
HOSTNAME_SET=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --apt) APT_ID="${2:-}"; shift 2;;
    --url) PKDR_URL="${2:-}"; shift 2;;
    --hostname) HOSTNAME_SET="${2:-}"; shift 2;;
    -h|--help)
      sed -n '1,120p' "$0"
      exit 0
      ;;
    *)
      die "Unknown argument: $1"
      ;;
  esac
done

require_root
[[ -n "${APT_ID}" ]] || die "--apt is required (e.g., 01, 07)"
[[ -n "${PKDR_URL}" ]] || die "--url is required"

# --- constants ---
PI_USER="pi"
PI_UID="1000"
PI_HOME="/home/${PI_USER}"

ENV_FILE="/etc/pkdr-kiosk.env"
SWAY_DIR="${PI_HOME}/.config/sway"
SWAY_CONF="${SWAY_DIR}/pkdr-kiosk.conf"
UNIT_FILE="/etc/systemd/system/pkdr-cage-kiosk.service"
LAUNCHER="/usr/local/bin/pkdr-launch-chromium.sh"

backup_if_exists() {
  local f="$1"
  if [[ -e "$f" ]]; then
    local b="${f}.$(ts)"
    log "Backing up ${f} -> ${b}"
    cp -a -- "$f" "$b"
  fi
}

write_env() {
  backup_if_exists "$ENV_FILE"
  log "Writing ${ENV_FILE}"
  cat >"$ENV_FILE" <<EOF
# Park Drive kiosk host-specific configuration
PKDR_APT=${APT_ID}
PKDR_URL=${PKDR_URL}
EOF
  chmod 0644 "$ENV_FILE"
  chown root:root "$ENV_FILE"
}

write_sway_conf() {
  log "Ensuring ${SWAY_DIR} exists"
  install -d -m 0755 -o "${PI_USER}" -g "${PI_USER}" "$SWAY_DIR"

  backup_if_exists "$SWAY_CONF"
  log "Writing ${SWAY_CONF}"
  cat >"$SWAY_CONF" <<'EOF'
# /home/pi/.config/sway/pkdr-kiosk.conf
# ---- Park Drive Kiosk Sway Config ----

set $mod Mod4
set $term /bin/false
set $out DSI-1

bar { mode invisible }
output * bg #000000 solid_color
output $out transform 270

# Touch mapping (generic + device-specific)
input type:touch map_to_output $out
input "10-005d Goodix Capacitive TouchScreen" map_to_output $out
input "10-0038 generic ft5x06 (79)" map_to_output $out
input "11-0038 generic ft5x06 (79)" map_to_output $out
input "6-0038 generic ft5x06 (79)"  map_to_output $out
input "4-0038 generic ft5x06 (79)"  map_to_output $out

# Disable VT switching + common escapes
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

# Chromium must stay fullscreen
for_window [app_id="chromium"] fullscreen enable
for_window [class="Chromium"] fullscreen enable
for_window [app_id="chromium"] floating disable
for_window [class="Chromium"] floating disable

exec_always /usr/local/bin/pkdr-launch-chromium.sh
EOF
  chown "${PI_USER}:${PI_USER}" "$SWAY_CONF"
  chmod 0644 "$SWAY_CONF"
}

write_unit() {
  backup_if_exists "$UNIT_FILE"
  log "Writing ${UNIT_FILE}"
  cat >"$UNIT_FILE" <<EOF
[Unit]
Description=Park Drive Kiosk (Sway + Chromium) Apt${APT_ID}
After=systemd-user-sessions.service systemd-logind.service dbus.service plymouth-quit-wait.service
Wants=systemd-user-sessions.service systemd-logind.service dbus.service
Conflicts=display-manager.service getty@tty1.service
Before=getty@tty1.service

[Service]
Type=simple
User=${PI_USER}

PAMName=login
SupplementaryGroups=video input render tty
Environment=LIBSEAT_BACKEND=logind

# Own tty1
TTYPath=/dev/tty1
TTYReset=yes
TTYVHangup=yes
TTYVTDisallocate=yes
StandardInput=tty

# Logging
StandardOutput=journal
StandardError=journal

# Faster, deterministic restarts
KillMode=control-group
TimeoutStopSec=2
SendSIGKILL=yes
Restart=always
RestartSec=2

# Environment
Environment=HOME=${PI_HOME}
Environment=XDG_RUNTIME_DIR=/run/user/${PI_UID}

# Ensure runtime exists (system service, no “desktop login”)
ExecStartPre=+/usr/bin/mkdir -p /run/user/${PI_UID}
ExecStartPre=+/usr/bin/chown ${PI_USER}:${PI_USER} /run/user/${PI_UID}
ExecStartPre=+/usr/bin/chmod 0700 /run/user/${PI_UID}
ExecStartPre=+/usr/bin/chvt 1

# Start sway kiosk
ExecStart=/usr/bin/sway --config ${SWAY_CONF}

[Install]
WantedBy=graphical.target
EOF
  chmod 0644 "$UNIT_FILE"
  chown root:root "$UNIT_FILE"
}

fix_launcher_perms() {
  if [[ ! -e "$LAUNCHER" ]]; then
    log "WARNING: ${LAUNCHER} does not exist yet. Skipping chmod/chown."
    return 0
  fi
  log "Ensuring permissions on ${LAUNCHER} (root:root 0755)"
  chown root:root "$LAUNCHER"
  chmod 0755 "$LAUNCHER"
}

maybe_set_hostname() {
  [[ -n "${HOSTNAME_SET}" ]] || return 0
  log "Setting hostname -> ${HOSTNAME_SET}"
  hostnamectl set-hostname "${HOSTNAME_SET}"
}

reload_and_restart() {
  log "systemctl daemon-reload"
  systemctl daemon-reload

  log "Enable pkdr-cage-kiosk.service"
  systemctl enable pkdr-cage-kiosk.service >/dev/null

  log "Restart pkdr-cage-kiosk.service"
  systemctl restart pkdr-cage-kiosk.service

  log "Status:"
  systemctl status pkdr-cage-kiosk.service --no-pager || true
}

sanity() {
  log "Sanity: chromium processes (if any):"
  pgrep -a chromium || true

  log "Sanity: touch controllers:"
  grep -RIn "Goodix" /proc/bus/input/devices || true
  grep -RIn "ft5x06" /proc/bus/input/devices || true
}

main() {
  write_env
  write_sway_conf
  write_unit
  fix_launcher_perms
  maybe_set_hostname
  reload_and_restart
  sanity
  log "Done."
}

main
