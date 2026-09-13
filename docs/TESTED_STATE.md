# Tested production state — 2026-09-13

Author: **Marcin Kowalik <mkowalik@agh.edu.pl>**

Validated raw stream:

```text
~111.11 Hz
6667 samples / ~60.00 s
bad_reports=0
idle std ~2.9-3.7 counts
idle max_step ~7-10 counts
```

Validated RAM-first event:

```text
trigger_utc: 2026-09-13T12:57:36.530921Z
end_utc: 2026-09-13T12:58:38.127012Z
trigger_vector_counts: 1669.8687
threshold: 50 counts / 3 samples
samples_saved: 10744
compressed_bytes: 131075
verified_in_ram: true
storage_stage: SD
SHA-256: 78d4141dbe2b7a62e065bb49b323405e4ff47965721a7b4b064a387322216862
```

During the event, only `/run/qcn/events/*.part` existed. After completion the RAM directory was empty and the verified `.csv.gz` + `.json` existed on SD. `gzip -t` passed and the on-disk SHA-256 matched metadata.

After full Raspberry Pi reboot, `qcn-recorder.service` returned active automatically and live acquisition returned ~111.11 Hz.

## HTTP API validation

Validated HTTP API from macOS over LAN:

```text
/sensors.json -> Quake-Catcher available=true
/qcn.json -> live XYZ, baseline, residual, trigger and event state
/sensors.csv -> valid single-row CSV
sensor-http-api.service -> active (running)
```

The API reads QCN state from `/run/qcn/latest.json`; it does not add a high-rate SD write path.
