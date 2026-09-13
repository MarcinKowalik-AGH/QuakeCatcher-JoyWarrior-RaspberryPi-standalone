# HTTP API

Author: **Marcin Kowalik <mkowalik@agh.edu.pl>**

The optional `integration/http-api` component exposes current sensor data as JSON and CSV on port 80.

Validated on 2026-09-13 from both the Raspberry Pi and a macOS client.

## Tested URLs

```text
http://<raspberry-ip>/
http://<raspberry-ip>/sensors.json
http://<raspberry-ip>/sensors.csv
http://<raspberry-ip>/radioactive.json
http://<raspberry-ip>/radioactive.csv
http://<raspberry-ip>/qcn.json
http://<raspberry-ip>/qcn.csv
http://<raspberry-ip>/qcn/event/latest.json
```

The root endpoint is plain text. JSON is recommended for web integrations; CSV is convenient for simple scripts and spreadsheets.

The server reads existing sensor files only; it does not create a separate acquisition database.

See [`../../integration/http-api/README.md`](../../integration/http-api/README.md) for installation and security notes.
