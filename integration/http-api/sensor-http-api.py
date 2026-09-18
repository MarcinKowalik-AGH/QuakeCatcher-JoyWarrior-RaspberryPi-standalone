#!/usr/bin/python3
#
# Raspberry Pi Radioactive@Home + Quake-Catcher HTTP API
#
# Author: Marcin Kowalik
# E-mail: mkowalik@agh.edu.pl
# SPDX-License-Identifier: MIT
#
# Read-only local HTTP API. It does not write sensor data and disables
# per-request HTTP logging to avoid unnecessary microSD writes.
#

import csv
import glob
import gzip
import io
import json
import os
import socket
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


HOST = "0.0.0.0"
PORT = 80
API_VERSION = "1.1"

RADIOACTIVE_CSV = "/opt/radioactive/measurements.csv"
RADIOACTIVE_ARCHIVE = "/opt/radioactive/archive"
QCN_LIVE = "/run/qcn/latest.json"
QCN_EVENTS = "/var/lib/qcn/events"


def utcnow():
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def int_or_none(value):
    return int(value) if value not in (None, "") else None


def float_or_none(value):
    return float(value) if value not in (None, "") else None


def parse_radioactive_row(row):
    return {
        "timestamp_utc": row.get("timestamp_utc"),
        "timer_ms": int_or_none(row.get("timer_ms")),
        "counter": int_or_none(row.get("counter")),
        "delta_ms": int_or_none(row.get("delta_ms")),
        "delta_counts": int_or_none(row.get("delta_counts")),
        "cpm": float_or_none(row.get("cpm")),
        "dose_uSv_h_est": float_or_none(row.get("dose_uSv_h_est")),
        "revision": int_or_none(row.get("revision")),
        "device_id": int_or_none(row.get("device_id")),
        "status": row.get("status"),
    }


def valid_radioactive_measurement(row):
    return (
        row.get("status") == "ok"
        and row.get("cpm") not in (None, "")
        and row.get("dose_uSv_h_est") not in (None, "")
    )


def find_latest_valid(rows):
    for row in reversed(rows):
        if valid_radioactive_measurement(row):
            return parse_radioactive_row(row)
    return None


def read_archived_latest_valid():
    files = glob.glob(os.path.join(RADIOACTIVE_ARCHIVE, "measurements.csv-*"))
    files.sort(key=os.path.getmtime, reverse=True)

    for path in files:
        try:
            opener = gzip.open if path.endswith(".gz") else open
            with opener(path, "rt", newline="") as f:
                rows = list(csv.DictReader(f))
            latest = find_latest_valid(rows)
            if latest:
                return latest
        except Exception:
            continue

    return None


def read_radioactive():
    result = {"available": False}

    try:
        with open(RADIOACTIVE_CSV, "r", newline="") as f:
            rows = list(csv.DictReader(f))

        if not rows:
            return result

        current = parse_radioactive_row(rows[-1])
        latest_valid = find_latest_valid(rows)

        if latest_valid is None:
            latest_valid = read_archived_latest_valid()

        current_has_value = (
            current.get("cpm") is not None
            and current.get("dose_uSv_h_est") is not None
        )
        effective = current if current_has_value else latest_valid
        using_last_valid = (not current_has_value) and latest_valid is not None

        return {
            "available": True,
            # Current sensor/recorder state. These fields remain backward-compatible.
            "timestamp_utc": current.get("timestamp_utc"),
            "timer_ms": current.get("timer_ms"),
            "counter": current.get("counter"),
            "delta_ms": current.get("delta_ms"),
            "delta_counts": current.get("delta_counts"),
            "cpm": effective.get("cpm") if effective else None,
            "dose_uSv_h_est": effective.get("dose_uSv_h_est") if effective else None,
            "revision": current.get("revision"),
            "device_id": current.get("device_id"),
            "status": current.get("status"),
            # Source of the value exposed in cpm/dose_uSv_h_est.
            "measurement_timestamp_utc": (
                effective.get("timestamp_utc") if effective else None
            ),
            "using_last_valid": using_last_valid,
            # Explicit state for consumers that need to distinguish current vs value.
            "current": current,
            "latest_valid": latest_valid,
        }

    except Exception as e:
        result["error"] = str(e)
        return result


def read_qcn():
    result = {"available": False}

    try:
        with open(QCN_LIVE, "r") as f:
            data = json.load(f)

        data["available"] = True
        return data

    except Exception as e:
        result["error"] = str(e)
        return result


def read_latest_event():
    result = {"available": False}

    try:
        files = glob.glob(os.path.join(QCN_EVENTS, "event-*.json"))

        if not files:
            return result

        latest = max(files, key=os.path.getmtime)

        with open(latest, "r") as f:
            data = json.load(f)

        data["available"] = True
        data["metadata_file"] = os.path.basename(latest)
        return data

    except Exception as e:
        result["error"] = str(e)
        return result


def combined():
    return {
        "generated_utc": utcnow(),
        "hostname": socket.gethostname(),
        "api_version": API_VERSION,
        "author": "Marcin Kowalik",
        "email": "mkowalik@agh.edu.pl",
        "radioactive": read_radioactive(),
        "quakecatcher": read_qcn(),
    }


def dict_to_csv(data):
    out = io.StringIO()
    fields = list(data.keys())
    writer = csv.DictWriter(out, fieldnames=fields)
    writer.writeheader()
    writer.writerow(data)
    return out.getvalue()


def radioactive_csv():
    rad = read_radioactive()
    current = rad.get("current") or {}
    latest_valid = rad.get("latest_valid") or {}

    row = {
        "available": rad.get("available"),
        "timestamp_utc": rad.get("timestamp_utc"),
        "timer_ms": rad.get("timer_ms"),
        "counter": rad.get("counter"),
        "delta_ms": rad.get("delta_ms"),
        "delta_counts": rad.get("delta_counts"),
        "cpm": rad.get("cpm"),
        "dose_uSv_h_est": rad.get("dose_uSv_h_est"),
        "revision": rad.get("revision"),
        "device_id": rad.get("device_id"),
        "status": rad.get("status"),
        "measurement_timestamp_utc": rad.get("measurement_timestamp_utc"),
        "using_last_valid": int(bool(rad.get("using_last_valid"))),
        "current_cpm": current.get("cpm"),
        "current_dose_uSv_h_est": current.get("dose_uSv_h_est"),
        "latest_valid_timestamp_utc": latest_valid.get("timestamp_utc"),
    }
    return dict_to_csv(row)


def sensors_csv():
    rad = read_radioactive()
    qcn = read_qcn()

    row = {
        "generated_utc": utcnow(),
        "radioactive_timestamp_utc": rad.get("timestamp_utc"),
        "radioactive_measurement_timestamp_utc": rad.get("measurement_timestamp_utc"),
        "radioactive_cpm": rad.get("cpm"),
        "radioactive_uSv_h": rad.get("dose_uSv_h_est"),
        "radioactive_counter": rad.get("counter"),
        "radioactive_status": rad.get("status"),
        "radioactive_using_last_valid": int(bool(rad.get("using_last_valid"))),
        "qcn_timestamp_utc": qcn.get("timestamp_utc"),
        "qcn_x": qcn.get("x"),
        "qcn_y": qcn.get("y"),
        "qcn_z": qcn.get("z"),
        "qcn_residual": qcn.get("residual_vector_counts"),
        "qcn_event_active": qcn.get("event_active"),
        "qcn_trigger": qcn.get("trigger_threshold_counts"),
    }

    return dict_to_csv(row)


class Handler(BaseHTTPRequestHandler):
    server_version = f"MarcinKowalik-SensorAPI/{API_VERSION}"

    def log_message(self, fmt, *args):
        pass

    def send_common_headers(self, content_type):
        self.send_header("Content-Type", content_type)
        self.send_header("Cache-Control", "no-store, no-cache, must-revalidate")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("X-Author", "Marcin Kowalik")
        self.send_header("X-Sensor-API-Version", API_VERSION)

    def send_json(self, obj, status=200):
        body = (json.dumps(obj, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
        self.send_response(status)
        self.send_common_headers("application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def send_text(self, text, content_type):
        body = text.encode("utf-8")
        self.send_response(200)
        self.send_common_headers(content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        path = self.path.split("?", 1)[0]

        if path == "/":
            self.send_text(f"""Marcin Kowalik sensor station

Radioactive@Home + Quake-Catcher
Sensor API version: {API_VERSION}

Author: Marcin Kowalik
E-mail: mkowalik@agh.edu.pl

Endpoints:

/sensors.json
/sensors.csv

/radioactive.json
/radioactive.csv

/qcn.json
/qcn.csv

/xcn/event/latest.json
""", "text/plain; charset=utf-8")
            return

        if path == "/sensors.json":
            self.send_json(combined()); return
        if path == "/sensors.csv":
            self.send_text(sensors_csv(), "text/csv; charset=utf-8"); return
        if path == "/radioactive.json":
            self.send_json(read_radioactive()); return
        if path == "/radioactive.csv":
            self.send_text(radioactive_csv(), "text/csv; charset=utf-8"); return
        if path == "/qcn.json":
            self.send_json(read_qcn()); return
        if path == "/qcn.csv":
            self.send_text(dict_to_csv(read_qcn()), "text/csv; charset=utf-8"); return
        if path == "/qcn/event/latest.json":
            self.send_json(read_latest_event()); return

        self.send_json({"error": "not found", "path": path}, status=404)


if __name__ == "__main__":
    server = ThreadingHTTPServer((HOST, PORT), Handler)
    print(f"Sensor HTTP API {API_VERSION} listening on {HOST}:{PORT}", flush=True)
    server.serve_forever()
