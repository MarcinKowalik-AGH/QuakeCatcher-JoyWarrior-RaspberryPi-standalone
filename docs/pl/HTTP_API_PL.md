# HTTP API

Autor: **Marcin Kowalik <mkowalik@agh.edu.pl>**

Opcjonalny moduł `integration/http-api` wystawia bieżące dane sensorów w JSON i CSV na porcie 80.

Został zweryfikowany 13.09.2026 zarówno lokalnie na Raspberry Pi, jak i z klienta macOS w tej samej sieci LAN.

## Zweryfikowane adresy

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

Endpoint `/` zwraca zwykły tekst. Do integracji WWW zalecany jest JSON; CSV jest wygodny do prostych skryptów i arkuszy.

Serwer tylko odczytuje istniejące pliki sensorów. Nie tworzy osobnej bazy pomiarowej i nie loguje każdego zapytania.

Instalacja i uwagi bezpieczeństwa: [`../../integration/http-api/README_PL.md`](../../integration/http-api/README_PL.md).
