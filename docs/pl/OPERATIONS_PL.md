# Eksploatacja — QCN RAM-first

Autor: **Marcin Kowalik <mkowalik@agh.edu.pl>**

## Polecenia

```bash
qcnctl status
qcnctl live
qcnctl events
qcnctl latest-event
qcnctl verify-latest
qcnctl storage
qcnctl config
qcnctl threshold
sudo qcnctl threshold 50
sudo qcnctl prune
```

## Event

Aktywny event powstaje w `/run/qcn/events/*.part`. Na SD nie ma nowego eventu do chwili zakończenia. Po zamknięciu gzip jest weryfikowany w RAM, liczba rekordów jest porównywana, liczony jest SHA-256, a dopiero potem pliki są atomowo kopiowane do `/var/lib/qcn/events`.

Awaria zasilania w trakcie zdarzenia może utracić tylko bieżący event z RAM; nie pozostawia celowo częściowego eventu jako kompletnego pliku na SD.

## Stan HTTP API

Jeżeli zainstalowano opcjonalne API:

```bash
systemctl status sensor-http-api.service --no-pager
curl -s http://127.0.0.1/sensors.json | python3 -m json.tool
```
