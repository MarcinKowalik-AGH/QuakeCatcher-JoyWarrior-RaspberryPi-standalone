# HTTP API

Autor: **Marcin Kowalik <mkowalik@agh.edu.pl>**

Opcjonalny moduł `integration/http-api` wystawia dane sensorów jako JSON i CSV na TCP/80.

**Aktualna wersja API: 1.1 — zweryfikowana 18.09.2026.**

## Adresy

```text
http://<ip-raspberry>/
http://<ip-raspberry>/sensors.json
http://<ip-raspberry>/sensors.csv
http://<ip-raspberry>/radioactive.json
http://<ip-raspberry>/radioactive.csv
http://<ip-raspberry>/qcn.json
http://<ip-raspberry>/qcn.csv
http://<ip-raspberry>/qcn/event/latest.json
```

Dla Radioactive@Home API 1.1 rozdziela bieżący stan recordera od wartości pomiarowej. Podczas `reset` lub `baseline` pola `cpm` i `dose_uSv_h_est` zachowują ostatnią prawidłową wartość, natomiast `status`, `current`, `measurement_timestamp_utc` oraz `using_last_valid` jednoznacznie pokazują jej pochodzenie. W razie potrzeby API szuka ostatniego prawidłowego pomiaru także w obróconych archiwach CSV.

Pełny opis: [`../../integration/http-api/README_PL.md`](../../integration/http-api/README_PL.md).
