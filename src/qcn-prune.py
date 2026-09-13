#!/usr/bin/python3
# Quake-Catcher persistent event retention
# Author: Marcin Kowalik <mkowalik@agh.edu.pl>
# Copyright (c) 2026 Marcin Kowalik
# SPDX-License-Identifier: MIT

import json
import os
import shutil
import time
from pathlib import Path

EVENT_DIR = Path("/var/lib/qcn/events")
MAX_AGE_DAYS = int(os.environ.get("QCN_EVENT_MAX_AGE_DAYS", "365"))
MAX_TOTAL_BYTES = int(os.environ.get("QCN_EVENT_MAX_BYTES", str(2 * 1024 * 1024 * 1024)))
MIN_FREE_BYTES = int(os.environ.get("QCN_MIN_FREE_BYTES", str(4 * 1024 * 1024 * 1024)))
ORPHAN_GRACE_SEC = int(os.environ.get("QCN_ORPHAN_GRACE_SEC", "86400"))
CUTOFF = time.time() - MAX_AGE_DAYS * 86400


def status(meta):
    try:
        with open(meta, "r", encoding="utf-8") as f:
            return json.load(f).get("status", "")
    except Exception:
        return ""


def remove_path(path):
    try:
        if path.exists():
            print("delete:", path)
            path.unlink()
    except Exception as exc:
        print("ERROR:", path, exc)


def remove_event(event):
    remove_path(event["data"])
    remove_path(event["meta"])


def filesystem_free():
    return shutil.disk_usage("/").free


EVENT_DIR.mkdir(parents=True, exist_ok=True)
events = []

for meta in EVENT_DIR.glob("event-*.json"):
    data = meta.with_suffix(".csv.gz")
    if status(meta) == "recording":
        continue
    ms = meta.stat()
    size = ms.st_size
    mtime = ms.st_mtime
    if data.exists():
        ds = data.stat()
        size += ds.st_size
        mtime = min(mtime, ds.st_mtime)
    events.append({"meta": meta, "data": data, "size": size, "mtime": mtime})

now = time.time()
for data in EVENT_DIR.glob("event-*.csv.gz"):
    meta = data.with_suffix("").with_suffix(".json")
    if not meta.exists() and now - data.stat().st_mtime > ORPHAN_GRACE_SEC:
        remove_path(data)

for meta in EVENT_DIR.glob("event-*.json"):
    data = meta.with_suffix(".csv.gz")
    if not data.exists() and now - meta.stat().st_mtime > ORPHAN_GRACE_SEC:
        remove_path(meta)

events.sort(key=lambda e: e["mtime"])
remaining = []
for event in events:
    if event["mtime"] < CUTOFF:
        remove_event(event)
    else:
        remaining.append(event)

remaining = [e for e in remaining if e["meta"].exists() or e["data"].exists()]
total = sum(e["size"] for e in remaining)

while total > MAX_TOTAL_BYTES and remaining:
    event = remaining.pop(0)
    total -= event["size"]
    remove_event(event)

while filesystem_free() < MIN_FREE_BYTES and remaining:
    event = remaining.pop(0)
    total -= event["size"]
    remove_event(event)

print("===== QCN STORAGE =====")
print(f"events: {max(total, 0) / 1024 / 1024:.1f} MiB")
print(f"event limit: {MAX_TOTAL_BYTES / 1024 / 1024:.0f} MiB")
print(f"max age: {MAX_AGE_DAYS} days")
print(f"free filesystem: {filesystem_free() / 1024 / 1024 / 1024:.2f} GiB")
print(f"minimum free: {MIN_FREE_BYTES / 1024 / 1024 / 1024:.0f} GiB")
