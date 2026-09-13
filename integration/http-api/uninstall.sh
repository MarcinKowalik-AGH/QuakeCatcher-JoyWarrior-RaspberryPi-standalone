#!/bin/bash
# Shared sensor HTTP API uninstaller
# Author: Marcin Kowalik <mkowalik@agh.edu.pl>
# SPDX-License-Identifier: MIT
set -euo pipefail
if [ "${EUID:-$(id -u)}" -ne 0 ]; then echo "Run through sudo." >&2; exit 1; fi
systemctl disable --now sensor-http-api.service 2>/dev/null || true
rm -f /etc/systemd/system/sensor-http-api.service /usr/local/sbin/sensor-http-api
systemctl daemon-reload
echo "sensor-http-api removed. Sensor data were not touched."
