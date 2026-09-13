# Shared local HTTP API

**Author:** Marcin Kowalik <mkowalik@agh.edu.pl>

This optional read-only component exposes the current Radioactive@Home and Quake-Catcher state over HTTP on TCP port 80. The same component is included in both sensor repositories because it can serve one sensor or both sensors from the same Raspberry Pi.

It does not log individual HTTP requests and does not create another sensor-data log. QCN live data are read from `/run/qcn/latest.json` (RAM); Radioactive data are read from the already existing `measurements.csv`.

## Install

```bash
sudo ./integration/http-api/install.sh
```

If port 80 is occupied, the installer stops and does not replace the other web service.

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

From another machine in the LAN, replace `127.0.0.1` with the Raspberry Pi address.

## Security

The service intentionally has no authentication and sends `Access-Control-Allow-Origin: *`. It is designed for a trusted LAN. Do **not** forward TCP/80 from the public Internet directly to this Raspberry Pi. Use a protected server-side relay, VPN, reverse proxy with authentication/TLS, or another controlled integration if remote publication is required.

The process runs as `www-data`; systemd grants only `CAP_NET_BIND_SERVICE` so it can bind port 80 without running as root.

## Uninstall

```bash
sudo ./integration/http-api/uninstall.sh
```

Sensor acquisition services and sensor data are not removed.
