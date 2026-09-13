# Quake-Catcher / JoyWarrior24F14 on Raspberry Pi — standalone RAM-first recorder

**Version:** `1.1.0`  
**Author:** **Marcin Kowalik**  
**E-mail:** **mkowalik@agh.edu.pl**  
**GitHub:** `MarcinKowalik-AGH`  
**Validated:** `2026-09-13`

This project preserves a legacy Quake-Catcher / JoyWarrior24F14 USB accelerometer as an independent Raspberry Pi seismic-event recorder. It reads the full raw HID stream, keeps high-rate working data in RAM, writes only batched summaries to microSD, and commits full event waveforms to SD only after the event is closed, gzip-verified and SHA-256 hashed.

> Preservation / reverse-engineering project by **Marcin Kowalik <mkowalik@agh.edu.pl>**. It is not an official continuation of the former Quake-Catcher Network project and is not affiliated with Code Mercenaries or BOINC.

## Validated hardware and software

```text
Host: Raspberry Pi 3 Model B Rev 1.2
OS: Raspberry Pi OS Lite 32-bit / Raspbian GNU/Linux 13 (trixie)
Kernel validated: 6.18.39+rpt-rpi-v7

Sensor: Code Mercenaries JoyWarrior24F14
USB VID:PID: 07c0:1116
Serial on validated unit: 000009F0
Raw HID interface: USB interface 1.0 (usually /dev/hidraw0)
Observed report length: 7 bytes
Observed sustained rate: ~111.11 Hz
```

## Raw HID report

```text
byte 0-1  X  uint16 little-endian
byte 2-3  Y  uint16 little-endian
byte 4-5  Z  uint16 little-endian
byte 6    status/buttons
```

Example:

```text
8c 20 b1 1f 0a 2f 00  ->  X=8332 Y=8113 Z=12042 status=0
```

The service discovers the device by VID/PID and interface path, not by a fixed `/dev/hidrawN` number.

## RAM-first design

```text
JoyWarrior raw HID (~111 Hz)
          |
          v
       /run/qcn  (tmpfs / RAM)
          |-- latest.json
          |-- 30 s pre-trigger ring buffer
          |-- baseline/noise state
          |-- active event .csv.gz.part + .json.part
          `-- minute summaries waiting for batch flush

When an event ends:
RAM gzip -> verify -> count samples -> SHA-256 -> atomic SD commit

Persistent SD:
/var/lib/qcn/summary.csv
/var/lib/qcn/events/event-*.csv.gz
/var/lib/qcn/events/event-*.json
```

## Validated default trigger

```text
vector threshold: 50 counts
consecutive samples: 3
pre-trigger: 30 s
post-trigger: 60 s
maximum event: 600 s
baseline calibration: 10 s
summary interval: 60 s
summary SD flush: 900 s (15 min)
```

Observed idle noise during validation was ~3 counts standard deviation per axis and ~8-10 counts max step. A controlled table tap produced trigger vectors hundreds to >1000 counts, giving substantial margin above idle noise.

## Quick installation

```bash
git clone https://github.com/MarcinKowalik-AGH/QuakeCatcher-JoyWarrior-RaspberryPi-standalone.git
cd QuakeCatcher-JoyWarrior-RaspberryPi-standalone
sudo ./scripts/install.sh
qcnctl status
```

## Control

```bash
qcnctl status
qcnctl live
qcnctl events
qcnctl latest-event
qcnctl verify-latest
qcnctl storage
qcnctl config
qcnctl threshold
sudo qcnctl threshold 50
sudo qcnctl prune
```

## microSD protection

- high-rate raw stream: never continuously written to SD;
- active event: RAM only;
- event is committed to SD only after successful gzip verification and SHA-256 computation;
- minute summaries: RAM, batched SD flush every 15 minutes;
- events: max 2 GiB, max age 365 days;
- oldest events are removed if free space on `/` falls below 4 GiB;
- summary log: monthly rotation, 24 rotations;
- system journal: optional bounded configuration included.

## Optional local HTTP API

A validated read-only HTTP API can expose the current Quake-Catcher and (when installed) Radioactive@Home state on a trusted LAN:

```text
/sensors.json
/sensors.csv
/radioactive.json
/radioactive.csv
/qcn.json
/qcn.csv
/qcn/event/latest.json
```

Install it separately so the core detector setup does not claim port 80 automatically:

```bash
sudo ./integration/http-api/install.sh
```

The API runs as `www-data`, receives only `CAP_NET_BIND_SERVICE`, suppresses per-request logging, and does not create another sensor-data log. It was validated from macOS against the Raspberry Pi on 2026-09-13. Do not forward this unauthenticated port directly from the public Internet.

See [`docs/en/HTTP_API.md`](docs/en/HTTP_API.md).

## Documentation

Polish: [`README_PL.md`](README_PL.md), [`docs/pl/`](docs/pl/)  
English: [`docs/en/`](docs/en/)

## Author

**Marcin Kowalik**  
**mkowalik@agh.edu.pl**

## License

MIT License.
