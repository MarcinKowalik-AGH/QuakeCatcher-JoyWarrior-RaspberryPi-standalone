#!/bin/bash
# Quake-Catcher / JoyWarrior24F14 RAM-first installer
# Author: Marcin Kowalik <mkowalik@agh.edu.pl>
# SPDX-License-Identifier: MIT
set -euo pipefail

if [ "${EUID:-$(id -u)}" -ne 0 ]; then
    echo "Run: sudo ./scripts/install.sh" >&2
    exit 1
fi

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
TS="$(date +%Y%m%d_%H%M%S)"
BACKUP="/root/qcn-backup-$TS"
mkdir -p "$BACKUP"

backup_if_exists() {
    local src="$1"
    if [ -e "$src" ]; then
        mkdir -p "$BACKUP$(dirname "$src")"
        cp -a "$src" "$BACKUP$src"
    fi
}

for cmd in python3 gzip sha256sum logrotate lsusb; do
    if ! command -v "$cmd" >/dev/null 2>&1; then
        echo "Missing dependency: $cmd" >&2
        echo "Install: sudo apt update && sudo apt install -y python3 gzip coreutils logrotate usbutils" >&2
        exit 1
    fi
done

if ! lsusb | grep -qi '07c0:1116'; then
    echo "WARNING: JoyWarrior24F14 07c0:1116 is not currently visible by USB."
fi

for f in /usr/local/sbin/qcn-recorder /usr/local/sbin/qcn-prune /usr/local/sbin/qcnctl /etc/qcn-recorder.conf /etc/systemd/system/qcn-recorder.service /etc/systemd/system/qcn-prune.service /etc/systemd/system/qcn-prune.timer /etc/logrotate.d/qcn-data /etc/systemd/journald.conf.d/sensor-limits.conf; do
    backup_if_exists "$f"
done

echo "Backup: $BACKUP"

systemctl stop qcn-recorder.service 2>/dev/null || true
systemctl stop qcn-prune.timer 2>/dev/null || true

install -d -m 0755 /usr/local/sbin /var/lib/qcn/events /var/lib/qcn/archive /etc/systemd/journald.conf.d
install -m 0755 "$ROOT/src/qcn-recorder.py" /usr/local/sbin/qcn-recorder
install -m 0755 "$ROOT/src/qcn-prune.py" /usr/local/sbin/qcn-prune
install -m 0755 "$ROOT/scripts/qcnctl" /usr/local/sbin/qcnctl

if [ ! -f /etc/qcn-recorder.conf ]; then
    install -m 0644 "$ROOT/config/qcn-recorder.conf" /etc/qcn-recorder.conf
else
    echo "Preserving existing /etc/qcn-recorder.conf"
fi

install -m 0644 "$ROOT/systemd/qcn-recorder.service" /etc/systemd/system/qcn-recorder.service
install -m 0644 "$ROOT/systemd/qcn-prune.service" /etc/systemd/system/qcn-prune.service
install -m 0644 "$ROOT/systemd/qcn-prune.timer" /etc/systemd/system/qcn-prune.timer
install -m 0644 "$ROOT/logrotate/qcn-data" /etc/logrotate.d/qcn-data
install -m 0644 "$ROOT/journald/sensor-limits.conf" /etc/systemd/journald.conf.d/sensor-limits.conf

python3 -m py_compile /usr/local/sbin/qcn-recorder /usr/local/sbin/qcn-prune
systemctl daemon-reload
systemctl restart systemd-journald
systemctl enable --now qcn-recorder.service
systemctl enable --now qcn-prune.timer

sleep 3

echo
echo "===== QCN RECORDER ====="
systemctl --no-pager --full status qcn-recorder.service || true
echo
echo "===== LIVE ====="
cat /run/qcn/latest.json 2>/dev/null || true
echo
echo "===== STORAGE ====="
systemctl start qcn-prune.service || true
journalctl -u qcn-prune.service -n 20 --no-pager || true

echo
echo "Installation complete."
echo "Version: $PROJECT_VERSION"
echo "Author: Marcin Kowalik <mkowalik@agh.edu.pl>"
echo "Status: qcnctl status"
echo "Backup: $BACKUP"
