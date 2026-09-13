#!/bin/bash
# Quake-Catcher standalone uninstaller
# Author: Marcin Kowalik <mkowalik@agh.edu.pl>
# SPDX-License-Identifier: MIT
set -euo pipefail
if [[ $EUID -ne 0 ]]; then echo "Run through sudo."; exit 1; fi
PURGE=0
[[ "${1:-}" == "--purge-data" ]] && PURGE=1
systemctl disable --now qcn-recorder.service 2>/dev/null || true
systemctl disable --now qcn-prune.timer 2>/dev/null || true
rm -f /etc/systemd/system/qcn-recorder.service /etc/systemd/system/qcn-prune.service /etc/systemd/system/qcn-prune.timer
rm -f /usr/local/sbin/qcn-recorder /usr/local/sbin/qcn-prune /usr/local/sbin/qcnctl
rm -f /etc/logrotate.d/qcn-data
systemctl daemon-reload
if [[ $PURGE -eq 1 ]]; then
    rm -rf /var/lib/qcn
    echo "Software and QCN data removed."
else
    echo "Software removed; persistent QCN data preserved in /var/lib/qcn."
fi
