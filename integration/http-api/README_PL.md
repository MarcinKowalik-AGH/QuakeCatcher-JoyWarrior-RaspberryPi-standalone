# Wspólne lokalne HTTP API

**Autor:** Marcin Kowalik <mkowalik@agh.edu.pl>  
**Wersja API:** 1.1

Opcjonalny moduł tylko-do-odczytu wystawia stan Radioactive@Home i Quake-Catchera na TCP/80. Ten sam komponent znajduje się w obu repozytoriach.

Nie zapisuje osobnego logu pomiarowego i nie loguje każdego żądania. Dane QCN są czytane z `/run/qcn/latest.json` w RAM, a dane Radioactive z istniejącego `measurements.csv`.

## Ciągłość wartości Radioactive

Przy granicy historycznego 21-próbkowego bloku RADAC rozpoczyna nową sekwencję licznika/timera. Recorder prawidłowo zapisuje wtedy `status=reset`, ale taki rekord nie ma jeszcze nowego CPM ani µSv/h.

API 1.1 zachowuje informację o bieżącym stanie i równocześnie udostępnia ostatni prawidłowy pomiar:

- `status` i `timestamp_utc` — bieżący stan recordera;
- `cpm` i `dose_uSv_h_est` — bieżąca wartość, a przy `reset/baseline` ostatnia prawidłowa wartość `status=ok`;
- `measurement_timestamp_utc` — czas pomiaru, z którego pochodzą CPM i µSv/h;
- `using_last_valid` — `true`, gdy API podaje ostatni prawidłowy pomiar;
- `current` — pełny bieżący rekord;
- `latest_valid` — pełny ostatni prawidłowy rekord.

Jeżeli po rotacji bieżący CSV nie zawiera jeszcze żadnego rekordu `ok`, API sprawdza również najnowsze archiwa `measurements.csv-*`. Na całkowicie nowej instalacji wartości pozostają `null` tylko do czasu pierwszego rzeczywistego wyliczonego interwału.

CSV korzysta z tej samej wartości efektywnej i zawiera flagę `using_last_valid`.

## Instalacja / aktualizacja

```bash
sudo ./integration/http-api/install.sh
```

## Endpointy

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

Test:

```bash
curl -s http://127.0.0.1/sensors.json | python3 -m json.tool
curl -s http://127.0.0.1/sensors.csv
```

## Bezpieczeństwo

API nie ma uwierzytelniania i wysyła `Access-Control-Allow-Origin: *`. Jest przeznaczone do zaufanej sieci LAN. Proces działa jako `www-data` i otrzymuje tylko `CAP_NET_BIND_SERVICE`.

## Odinstalowanie

```bash
sudo ./integration/http-api/uninstall.sh
```
