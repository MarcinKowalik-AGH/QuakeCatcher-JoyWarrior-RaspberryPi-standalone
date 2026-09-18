# Shared local HTTP API

**Author:** Marcin Kowalik <mkowalik@agh.edu.pl>  
**API version:** 1.1

This optional read-only component exposes the current Radioactive@Home and Quake-Catcher state over HTTP on TCP port 80. The same component is included in both sensor repositories because it can serve one sensor or both sensors from the same Raspberry Pi.

It does not log individual HTTP requests and does not create another sensor-data log. QCN live data are read from `/run/qcn/latest.json` (RAM); Radioactive data are read from the existing `measurements.csv`.

## Radioactive value continuity

RADAC starts a new counter/timer sequence at the boundary of each legacy 21-sample work block. The recorder correctly records this as `reset`, but that row has no newly calculated CPM/dose value.

API 1.1 keeps the current state visible while also exposing the latest valid measurement:

- `status` and `timestamp_utc`: current recorder state;
- `cpm` and `dose_uSv_h_est`: current value when available, otherwise the last valid `status=ok` value;
- `measurement_timestamp_utc`: timestamp belonging to the CPM/dose value;
- `using_last_valid`: `true` when CPM/dose come from the preceding valid row;
- `current`: explicit latest recorder row;
- `latest_valid`: explicit latest valid calculated measurement.

If the current CSV contains no valid measurement after log rotation, the API also checks the newest archived `measurements.csv-*` files. On a completely fresh installation, CPM/dose remain null until the first real calculated interval exists.

The CSV endpoints use the same effective CPM/dose values and include a `using_last_valid` flag.

## Install / update

```bash
sudo ./integration/http-api/install.sh
```

If port 80 is occupied by another service, the installer stops instead of replacing it.

## Endpoints

```text
/
/sensors.json
/sensors.csv
/radioactive.json
/radioactive.csv
/qcn.json
/qcn.csv
/qcn/event/latest.json
```

Example:

```bash
curl -s http://127.0.0.1/sensors.json | python3 -m json.tool
curl -s http://127.0.0.1/sensors.csv
```

## Security

The service intentionally has no authentication and sends `Access-Control-Allow-Origin: *`. It is designed for a trusted LAN. Do not forward TCP/80 from the public Internet directly to the Raspberry Pi without an appropriate protected integration.

The process runs as `www-data`; systemd grants only `CAP_NET_BIND_SERVICE`.

## Uninstall

```bash
sudo ./integration/http-api/uninstall.sh
```

Sensor acquisition services and sensor data are not removed.
