# Format danych — Quake-Catcher

Autor: **Marcin Kowalik <mkowalik@agh.edu.pl>**

## RAW HID

7 bajtów: `<HHHB` little-endian: X, Y, Z, status. Środek osi 14-bitowych przyjmowany przez projekt: 8192.

## summary.csv

Jedna minuta statystyk: liczba próbek, Hz, średnie X/Y/Z, min/max, std, peak-to-peak, max_step i bad_reports.

## event CSV.gz

```text
timestamp_utc,timestamp_ns,x,y,z,status
```

JSON eventu zawiera trigger, baseline, liczbę próbek, rozmiar po kompresji, SHA-256, `verified_in_ram`, `storage_stage` i `status`.
