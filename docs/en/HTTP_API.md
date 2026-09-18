# HTTP API

Author: **Marcin Kowalik <mkowalik@agh.edu.pl>**

The optional `integration/http-api` component exposes sensor data as JSON and CSV on TCP/80.

**Current API version: 1.1 — validated 2026-09-18.**

## URLs

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

For Radioactive@Home, API 1.1 separates the current recorder state from the measurement value. During `reset` or `baseline`, top-level `cpm` and `dose_uSv_h_est` retain the latest valid calculated value, while `status`, `current`, `measurement_timestamp_utc` and `using_last_valid` show exactly where that value came from. The API can fall back to rotated measurement archives if needed.

See [`../../integration/http-api/README.md`](../../integration/http-api/README.md) for the full schema, installation and security notes.
