#!/bin/bash
# Quake-Catcher production health check
# Author: Marcin Kowalik <mkowalik@agh.edu.pl>
# SPDX-License-Identifier: MIT
set -u

echo "===== USB ====="
lsusb | grep -i '07c0:1116' || echo "ERROR: JoyWarrior24F14 not present"
echo
echo "===== SERVICE ====="
systemctl is-enabled qcn-recorder.service || true
systemctl is-active qcn-recorder.service || true
systemctl show qcn-recorder.service -p NRestarts -p MainPID -p ActiveState -p SubState
echo
echo "===== LIVE ====="
cat /run/qcn/latest.json 2>/dev/null || true
echo
echo "===== RAM SUMMARY ====="
tail -5 /run/qcn/summary-live.csv 2>/dev/null || true
echo
echo "===== SD SUMMARY ====="
tail -5 /var/lib/qcn/summary.csv 2>/dev/null || true
echo
echo "===== EVENTS ====="
ls -lht /var/lib/qcn/events 2>/dev/null | head
echo
echo "===== STORAGE ====="
df -h /
du -sh /var/lib/qcn 2>/dev/null || true

echo
echo "===== OPTIONAL HTTP API ====="
if systemctl cat sensor-http-api.service >/dev/null 2>&1; then
    systemctl is-enabled sensor-http-api.service || true
    systemctl is-active sensor-http-api.service || true
    if command -v python3 >/dev/null 2>&1; then
        python3 - <<'PY'
import json, urllib.request
try:
    data=json.load(urllib.request.urlopen("http://127.0.0.1/sensors.json", timeout=3))
    print("HTTP API: OK")
    print("generated_utc:", data.get("generated_utc"))
except Exception as e:
    print("HTTP API: ERROR:", e)
PY
    fi
else
    echo "sensor-http-api.service not installed (optional)"
fi
