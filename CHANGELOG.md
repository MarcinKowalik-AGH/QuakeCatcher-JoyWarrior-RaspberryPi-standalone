# Changelog

Author: **Marcin Kowalik <mkowalik@agh.edu.pl>**

## 1.1.0 — 2026-09-13

- Added optional shared read-only HTTP API on port 80 with JSON and CSV endpoints.
- Added hardened `sensor-http-api.service` running as `www-data` with only `CAP_NET_BIND_SERVICE`.
- Added API installer/uninstaller, Polish/English API manual and tested JSON/CSV examples.
- API validated locally and from macOS over LAN; QCN live data are read from `/run/qcn/latest.json`, preserving the RAM-first design.
- Core v1.0.0 RAW HID acquisition/event pipeline remains unchanged.

## 1.0.0 — 2026-09-13

Production-ready RAM-first release validated on real JoyWarrior24F14 hardware.

- Raw HID acquisition from `07c0:1116`, interface 0, 7-byte reports.
- Measured sustained rate ~111.11 reports/s with `bad_reports=0`.
- Baseline/noise tracking in RAM.
- Trigger threshold 50 counts, 3 consecutive samples; 30 s pre-trigger and 60 s post-trigger.
- Active event written/compressed entirely in `/run/qcn/events` (tmpfs/RAM).
- Gzip integrity check + sample-count verification + SHA-256 before commit to SD.
- Atomic payload/metadata commit to `/var/lib/qcn/events` only after event completion.
- Minute summaries buffered in RAM and fsynced to SD in 15-minute batches.
- Daily retention: max 2 GiB events, max 365 days, preserve at least 4 GiB free on `/`.
- Full reboot validation with automatic service recovery.
