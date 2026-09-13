#!/bin/bash
# Shared read-only sensor HTTP API installer
# Author: Marcin Kowalik <mkowalik@agh.edu.pl>
# SPDX-License-Identifier: MIT
set -euo pipefail

if [ "${EUID:-$(id -u)}" -ne 0 ]; then
    echo "Run: sudo ./integration/http-api/install.sh" >&2
    exit 1
fi

ROOT="$(cd "$(dirname "$0")" && pwd)"
TS="$(date +%Y%m%d_%H%M%S)"
BACKUP="/root/sensor-http-api-backup-$TS"
mkdir -p "$BACKUP"

backup_if_exists() {
    local src="$1"
    if [ -e "$src" ]; then
        mkdir -p "$BACKUP$(dirname "$src")"
        cp -a "$src" "$BACKUP$src"
    fi
}

for f in /usr/local/sbin/sensor-http-api /etc/systemd/system/sensor-http-api.service; do
    backup_if_exists "$f"
done

systemctl stop sensor-http-api.service 2>/dev/null || true

if ss -ltnp | grep -qE '(^|[[:space:]])[^[:space:]]*:80[[:space:]]'; then
    echo "ERROR: TCP port 80 is already in use by another service." >&2
    ss -ltnp | grep ':80 ' >&2 || true
    echo "Stop/reconfigure that service before installing this API." >&2
    exit 2
fi

install -m 0755 "$ROOT/sensor-http-api.py" /usr/local/sbin/sensor-http-api
install -m 0644 "$ROOT/sensor-http-api.service" /etc/systemd/system/sensor-http-api.service

python3 -m py_compile /usr/local/sbin/sensor-http-api
systemctl daemon-reload
systemctl enable --now sensor-http-api.service

sleep 2

echo "===== SENSOR HTTP API ====="
systemctl --no-pager --full status sensor-http-api.service || true
echo
echo "Local test:"
python3 - <<'PY'
import urllib.request
print(urllib.request.urlopen("http://127.0.0.1/sensors.json", timeout=5).read().decode())
PY
echo
echo "Backup: $BACKUP"
echo "Author: Marcin Kowalik <mkowalik@agh.edu.pl>"
