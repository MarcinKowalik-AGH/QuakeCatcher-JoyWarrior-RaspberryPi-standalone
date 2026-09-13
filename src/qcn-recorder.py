#!/usr/bin/python3
#
# Quake-Catcher / JoyWarrior24F14 RAM-first recorder
# Author: Marcin Kowalik <mkowalik@agh.edu.pl>
# Copyright (c) 2026 Marcin Kowalik
# SPDX-License-Identifier: MIT
#
# RAW samples, baseline, pre-trigger buffer and the active event live in RAM.
# Only verified, closed event archives and batched summaries are committed to SD.

import csv
import gzip
import hashlib
import json
import math
import os
import select
import shutil
import signal
import struct
import sys
import time
from collections import deque
from datetime import datetime, timezone
from pathlib import Path

DATA_ROOT = Path("/var/lib/qcn")
SUMMARY = DATA_ROOT / "summary.csv"
EVENT_FINAL_DIR = DATA_ROOT / "events"

RUNTIME_DIR = Path("/run/qcn")
EVENT_RAM_DIR = RUNTIME_DIR / "events"
LATEST = RUNTIME_DIR / "latest.json"
SUMMARY_LIVE = RUNTIME_DIR / "summary-live.csv"

CENTER = 8192


def env_float(name, default):
    try:
        return float(os.environ.get(name, default))
    except Exception:
        return float(default)


def env_int(name, default):
    try:
        return int(os.environ.get(name, default))
    except Exception:
        return int(default)


TRIGGER_VECTOR = env_float("QCN_TRIGGER_VECTOR", 50.0)
TRIGGER_CONSECUTIVE = env_int("QCN_TRIGGER_CONSECUTIVE", 3)
PRETRIGGER_SEC = env_float("QCN_PRETRIGGER_SEC", 30.0)
POSTTRIGGER_SEC = env_float("QCN_POSTTRIGGER_SEC", 60.0)
MAX_EVENT_SEC = env_float("QCN_MAX_EVENT_SEC", 600.0)
BASELINE_CAL_SEC = env_float("QCN_BASELINE_CAL_SEC", 10.0)
BASELINE_ALPHA = env_float("QCN_BASELINE_ALPHA", 0.002)
SUMMARY_INTERVAL_SEC = env_float("QCN_SUMMARY_INTERVAL_SEC", 60.0)
SUMMARY_FLUSH_SEC = env_float("QCN_SUMMARY_FLUSH_SEC", 900.0)

PREBUFFER_SAMPLES = max(256, int(PRETRIGGER_SEC * 130.0))
STOP_REQUESTED = False

SUMMARY_HEADER = [
    "timestamp_utc", "samples", "duration_s", "sample_hz",
    "mean_x", "mean_y", "mean_z",
    "centered_x", "centered_y", "centered_z",
    "min_x", "max_x", "min_y", "max_y", "min_z", "max_z",
    "std_x", "std_y", "std_z",
    "p2p_x", "p2p_y", "p2p_z",
    "max_step", "bad_reports",
]


def utcnow():
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def utc_iso_from_ns(ns):
    return datetime.fromtimestamp(ns / 1e9, timezone.utc).isoformat().replace("+00:00", "Z")


def atomic_json(path, obj):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    with open(tmp, "w") as f:
        json.dump(obj, f, indent=2)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)


def fsync_dir(path):
    fd = os.open(path, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def copy_atomic_to_sd(src, dst):
    src = Path(src)
    dst = Path(dst)
    dst.parent.mkdir(parents=True, exist_ok=True)
    tmp = dst.with_name(dst.name + ".tmp")
    with open(src, "rb") as rf, open(tmp, "wb") as wf:
        shutil.copyfileobj(rf, wf, length=1024 * 1024)
        wf.flush()
        os.fsync(wf.fileno())
    os.replace(tmp, dst)
    fsync_dir(str(dst.parent))


def find_hidraw():
    base = Path("/sys/class/hidraw")
    if not base.is_dir():
        return None
    for entry in sorted(base.iterdir()):
        if not entry.name.startswith("hidraw"):
            continue
        sysdev = entry / "device"
        try:
            real = os.path.realpath(sysdev)
            uevent = (sysdev / "uevent").read_text().upper()
        except Exception:
            continue
        if "07C0" not in uevent or "1116" not in uevent:
            continue
        if ":1.0/" not in real:
            continue
        return "/dev/" + entry.name
    return None


def cleanup_runtime_parts():
    EVENT_RAM_DIR.mkdir(parents=True, exist_ok=True)
    for p in EVENT_RAM_DIR.iterdir():
        try:
            if p.is_file():
                p.unlink()
        except Exception:
            pass


class SummaryBuffer:
    def __init__(self):
        DATA_ROOT.mkdir(parents=True, exist_ok=True)
        RUNTIME_DIR.mkdir(parents=True, exist_ok=True)
        self.pending = []
        self.last_persistent_flush = time.monotonic()
        self._write_live_file()

    def _write_live_file(self):
        tmp = SUMMARY_LIVE.with_name(SUMMARY_LIVE.name + ".tmp")
        with open(tmp, "w", newline="") as f:
            w = csv.writer(f)
            w.writerow(SUMMARY_HEADER)
            w.writerows(self.pending)
        os.replace(tmp, SUMMARY_LIVE)

    def add(self, row):
        self.pending.append(row)
        self._write_live_file()
        if time.monotonic() - self.last_persistent_flush >= SUMMARY_FLUSH_SEC:
            self.flush_to_sd()

    def flush_to_sd(self):
        if not self.pending:
            self.last_persistent_flush = time.monotonic()
            return
        new_file = not SUMMARY.exists() or SUMMARY.stat().st_size == 0
        with open(SUMMARY, "a", newline="") as f:
            w = csv.writer(f)
            if new_file:
                w.writerow(SUMMARY_HEADER)
            w.writerows(self.pending)
            f.flush()
            os.fsync(f.fileno())
        self.pending.clear()
        self._write_live_file()
        self.last_persistent_flush = time.monotonic()


class Stats:
    def __init__(self):
        self.reset()

    def reset(self):
        self.start = time.monotonic()
        self.n = 0
        self.bad = 0
        self.total = [0.0, 0.0, 0.0]
        self.total2 = [0.0, 0.0, 0.0]
        self.minimum = [None, None, None]
        self.maximum = [None, None, None]
        self.previous = None
        self.max_step = 0.0

    def bad_report(self):
        self.bad += 1

    def add(self, x, y, z):
        values = (x, y, z)
        self.n += 1
        for i, value in enumerate(values):
            self.total[i] += value
            self.total2[i] += value * value
            if self.minimum[i] is None or value < self.minimum[i]:
                self.minimum[i] = value
            if self.maximum[i] is None or value > self.maximum[i]:
                self.maximum[i] = value
        if self.previous is not None:
            dx = x - self.previous[0]
            dy = y - self.previous[1]
            dz = z - self.previous[2]
            self.max_step = max(self.max_step, math.sqrt(dx * dx + dy * dy + dz * dz))
        self.previous = values

    def finish_row(self):
        duration = time.monotonic() - self.start
        if self.n == 0 or duration <= 0:
            self.reset()
            return None
        mean = [self.total[i] / self.n for i in range(3)]
        std = []
        for i in range(3):
            variance = self.total2[i] / self.n - mean[i] * mean[i]
            std.append(math.sqrt(max(variance, 0.0)))
        p2p = [self.maximum[i] - self.minimum[i] for i in range(3)]
        row = [
            utcnow(), self.n, f"{duration:.3f}", f"{self.n / duration:.3f}",
            f"{mean[0]:.3f}", f"{mean[1]:.3f}", f"{mean[2]:.3f}",
            f"{mean[0] - CENTER:.3f}", f"{mean[1] - CENTER:.3f}", f"{mean[2] - CENTER:.3f}",
            self.minimum[0], self.maximum[0], self.minimum[1], self.maximum[1],
            self.minimum[2], self.maximum[2],
            f"{std[0]:.3f}", f"{std[1]:.3f}", f"{std[2]:.3f}",
            p2p[0], p2p[1], p2p[2], f"{self.max_step:.3f}", self.bad,
        ]
        self.reset()
        return row


class EventCapture:
    def __init__(self):
        self.active = False
        self.gz = None
        self.writer = None

    def start(self, prebuffer, baseline, trigger_ns, trigger_vector, now_mono):
        EVENT_RAM_DIR.mkdir(parents=True, exist_ok=True)
        EVENT_FINAL_DIR.mkdir(parents=True, exist_ok=True)
        tag = datetime.fromtimestamp(trigger_ns / 1e9, timezone.utc).strftime("%Y%m%dT%H%M%S.%fZ")
        self.tag = tag
        self.ram_csv = EVENT_RAM_DIR / f"event-{tag}.csv.gz.part"
        self.ram_meta = EVENT_RAM_DIR / f"event-{tag}.json.part"
        self.final_csv = EVENT_FINAL_DIR / f"event-{tag}.csv.gz"
        self.final_meta = EVENT_FINAL_DIR / f"event-{tag}.json"
        self.gz = gzip.open(self.ram_csv, "wt", newline="")
        self.writer = csv.writer(self.gz)
        self.writer.writerow(["timestamp_utc", "timestamp_ns", "x", "y", "z", "status"])
        self.samples = 0
        for ns, x, y, z, status in prebuffer:
            self.writer.writerow([utc_iso_from_ns(ns), ns, x, y, z, status])
            self.samples += 1
        self.active = True
        self.start_mono = now_mono
        self.trigger_ns = trigger_ns
        self.trigger_vector = trigger_vector
        self.baseline = tuple(baseline)
        self.deadline = now_mono + POSTTRIGGER_SEC
        atomic_json(self.ram_meta, {
            "author": "Marcin Kowalik",
            "author_email": "mkowalik@agh.edu.pl",
            "device": "Code Mercenaries JoyWarrior24F14",
            "trigger_utc": utc_iso_from_ns(trigger_ns),
            "trigger_vector_counts": trigger_vector,
            "threshold_vector_counts": TRIGGER_VECTOR,
            "trigger_consecutive_samples": TRIGGER_CONSECUTIVE,
            "pretrigger_seconds": PRETRIGGER_SEC,
            "posttrigger_seconds": POSTTRIGGER_SEC,
            "baseline_xyz": list(self.baseline),
            "storage_stage": "RAM",
            "status": "recording",
        })

    def extend(self, now_mono):
        self.deadline = min(self.start_mono + MAX_EVENT_SEC, now_mono + POSTTRIGGER_SEC)

    def write(self, ns, x, y, z, status):
        if not self.active:
            return
        self.writer.writerow([utc_iso_from_ns(ns), ns, x, y, z, status])
        self.samples += 1

    def should_close(self, now_mono):
        return self.active and (now_mono >= self.deadline or now_mono - self.start_mono >= MAX_EVENT_SEC)

    def _verify_gzip_and_count(self):
        lines = 0
        with gzip.open(self.ram_csv, "rt") as f:
            for _ in f:
                lines += 1
        return max(0, lines - 1)

    def _sha256(self):
        h = hashlib.sha256()
        with open(self.ram_csv, "rb") as f:
            for chunk in iter(lambda: f.read(1024 * 1024), b""):
                h.update(chunk)
        return h.hexdigest()

    def close_and_commit(self, end_ns):
        if not self.active:
            return
        try:
            self.gz.close()
            self.gz = None
            verified_samples = self._verify_gzip_and_count()
            if verified_samples != self.samples:
                raise RuntimeError(f"RAM event verification mismatch: writer={self.samples}, gzip={verified_samples}")
            sha256 = self._sha256()
            compressed_bytes = self.ram_csv.stat().st_size
            complete_meta = {
                "author": "Marcin Kowalik",
                "author_email": "mkowalik@agh.edu.pl",
                "device": "Code Mercenaries JoyWarrior24F14",
                "trigger_utc": utc_iso_from_ns(self.trigger_ns),
                "end_utc": utc_iso_from_ns(end_ns),
                "trigger_vector_counts": self.trigger_vector,
                "threshold_vector_counts": TRIGGER_VECTOR,
                "trigger_consecutive_samples": TRIGGER_CONSECUTIVE,
                "pretrigger_seconds": PRETRIGGER_SEC,
                "posttrigger_seconds": POSTTRIGGER_SEC,
                "baseline_xyz": list(self.baseline),
                "samples_saved": self.samples,
                "compressed_bytes": compressed_bytes,
                "sha256_csv_gz": sha256,
                "verified_in_ram": True,
                "storage_stage": "committing_to_SD",
                "status": "complete",
            }
            atomic_json(self.ram_meta, complete_meta)
            copy_atomic_to_sd(self.ram_csv, self.final_csv)
            complete_meta["storage_stage"] = "SD"
            atomic_json(self.ram_meta, complete_meta)
            copy_atomic_to_sd(self.ram_meta, self.final_meta)
        finally:
            for p in (getattr(self, "ram_csv", None), getattr(self, "ram_meta", None)):
                if p:
                    try:
                        Path(p).unlink(missing_ok=True)
                    except Exception:
                        pass
            self.active = False
            self.writer = None
            self.gz = None


class Recorder:
    def __init__(self):
        cleanup_runtime_parts()
        DATA_ROOT.mkdir(parents=True, exist_ok=True)
        EVENT_FINAL_DIR.mkdir(parents=True, exist_ok=True)
        RUNTIME_DIR.mkdir(parents=True, exist_ok=True)
        self.summary = SummaryBuffer()
        self.capture = EventCapture()
        self.prebuffer = deque(maxlen=PREBUFFER_SAMPLES)

    def shutdown(self):
        self.summary.flush_to_sd()
        if self.capture.active:
            try:
                if self.capture.gz:
                    self.capture.gz.close()
            except Exception:
                pass
            for p in (getattr(self.capture, "ram_csv", None), getattr(self.capture, "ram_meta", None)):
                if p:
                    try:
                        Path(p).unlink(missing_ok=True)
                    except Exception:
                        pass

    def run(self):
        global STOP_REQUESTED
        while not STOP_REQUESTED:
            dev = find_hidraw()
            if dev is None:
                atomic_json(LATEST, {"timestamp_utc": utcnow(), "error": "JoyWarrior24F14 not found"})
                time.sleep(5)
                continue
            stats = Stats()
            fd = None
            last_latest = 0.0
            baseline = None
            calib_start = time.monotonic()
            calib_sum = [0.0, 0.0, 0.0]
            calib_n = 0
            trigger_run = 0
            try:
                fd = os.open(dev, os.O_RDONLY | os.O_NONBLOCK)
                while not STOP_REQUESTED:
                    ready, _, _ = select.select([fd], [], [], 0.5)
                    now_mono = time.monotonic()
                    if ready:
                        data = os.read(fd, 64)
                        if len(data) != 7:
                            stats.bad_report()
                            continue
                        x, y, z, status = struct.unpack("<HHHB", data)
                        ns = time.time_ns()
                        stats.add(x, y, z)
                        self.prebuffer.append((ns, x, y, z, status))
                        started_now = False
                        residual = None
                        if baseline is None:
                            calib_sum[0] += x; calib_sum[1] += y; calib_sum[2] += z; calib_n += 1
                            if now_mono - calib_start >= BASELINE_CAL_SEC and calib_n > 0:
                                baseline = [v / calib_n for v in calib_sum]
                                trigger_run = 0
                        else:
                            dx = x - baseline[0]; dy = y - baseline[1]; dz = z - baseline[2]
                            residual = math.sqrt(dx * dx + dy * dy + dz * dz)
                            if self.capture.active:
                                self.capture.write(ns, x, y, z, status)
                                if residual >= TRIGGER_VECTOR:
                                    self.capture.extend(now_mono)
                            else:
                                trigger_run = trigger_run + 1 if residual >= TRIGGER_VECTOR else 0
                                if trigger_run >= TRIGGER_CONSECUTIVE:
                                    self.capture.start(self.prebuffer, baseline, ns, residual, now_mono)
                                    started_now = True
                                    trigger_run = 0
                                if not started_now and residual < TRIGGER_VECTOR / 2.0:
                                    a = BASELINE_ALPHA
                                    baseline[0] = (1 - a) * baseline[0] + a * x
                                    baseline[1] = (1 - a) * baseline[1] + a * y
                                    baseline[2] = (1 - a) * baseline[2] + a * z
                        if self.capture.should_close(now_mono):
                            self.capture.close_and_commit(ns)
                            self.prebuffer.clear()
                            baseline = None
                            calib_start = now_mono
                            calib_sum = [0.0, 0.0, 0.0]
                            calib_n = 0
                            trigger_run = 0
                        if now_mono - last_latest >= 1.0:
                            obj = {
                                "timestamp_utc": utc_iso_from_ns(ns),
                                "device": dev,
                                "x": x, "y": y, "z": z,
                                "status": status,
                                "event_active": self.capture.active,
                                "event_stage": "RAM" if self.capture.active else None,
                                "trigger_threshold_counts": TRIGGER_VECTOR,
                                "summary_pending_in_ram": len(self.summary.pending),
                            }
                            if baseline is not None:
                                obj.update({
                                    "baseline_x": round(baseline[0], 3),
                                    "baseline_y": round(baseline[1], 3),
                                    "baseline_z": round(baseline[2], 3),
                                    "residual_vector_counts": round(residual, 3) if residual is not None else None,
                                })
                            else:
                                obj["baseline_state"] = "calibrating"
                            atomic_json(LATEST, obj)
                            last_latest = now_mono
                    if now_mono - stats.start >= SUMMARY_INTERVAL_SEC:
                        row = stats.finish_row()
                        if row:
                            self.summary.add(row)
            except Exception as e:
                atomic_json(LATEST, {
                    "timestamp_utc": utcnow(),
                    "device": dev,
                    "error": str(e),
                    "event_active": self.capture.active,
                })
                if self.capture.active:
                    try:
                        if self.capture.gz:
                            self.capture.gz.close()
                    except Exception:
                        pass
                    for p in (getattr(self.capture, "ram_csv", None), getattr(self.capture, "ram_meta", None)):
                        if p:
                            try:
                                Path(p).unlink(missing_ok=True)
                            except Exception:
                                pass
                    self.capture.active = False
                time.sleep(2)
            finally:
                if fd is not None:
                    try:
                        os.close(fd)
                    except Exception:
                        pass
        self.shutdown()


def handle_signal(signum, frame):
    global STOP_REQUESTED
    STOP_REQUESTED = True


if __name__ == "__main__":
    signal.signal(signal.SIGTERM, handle_signal)
    signal.signal(signal.SIGINT, handle_signal)
    Recorder().run()
