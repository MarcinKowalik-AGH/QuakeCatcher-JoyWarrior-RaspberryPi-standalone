# Wspólne lokalne HTTP API

**Autor:** Marcin Kowalik <mkowalik@agh.edu.pl>

To opcjonalny, tylko-do-odczytu moduł HTTP wystawiający bieżący stan Radioactive@Home i Quake-Catchera na porcie TCP 80. Ten sam komponent jest dołączony do obu repozytoriów, ponieważ na jednym Raspberry Pi może obsługiwać jeden sensor albo oba jednocześnie.

API nie zapisuje osobnego logu pomiarowego i celowo nie loguje każdego żądania HTTP. Dane QCN są czytane z `/run/qcn/latest.json` (RAM), a Radioactive z istniejącego `measurements.csv`.

## Instalacja

```bash
sudo ./integration/http-api/install.sh
```

Jeżeli port 80 jest już zajęty, instalator kończy działanie zamiast nadpisywać inną usługę WWW.

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

Test lokalny:

```bash
curl -s http://127.0.0.1/sensors.json | python3 -m json.tool
curl -s http://127.0.0.1/sensors.csv
```

Z innego komputera w LAN użyj adresu IP Raspberry Pi, np.:

```text
http://192.168.4.111/sensors.json
```

## Bezpieczeństwo

API nie ma uwierzytelniania i świadomie wysyła `Access-Control-Allow-Origin: *`. Jest przeznaczone do zaufanej sieci LAN. **Nie przekierowuj portu 80 z Internetu bezpośrednio na Raspberry Pi.** Do publikacji zdalnej użyj chronionego serwera pośredniczącego, VPN albo reverse proxy z TLS i uwierzytelnianiem.

Proces działa jako `www-data`; systemd nadaje mu tylko `CAP_NET_BIND_SERVICE`, dzięki czemu może otworzyć port 80 bez pracy jako root.

## Odinstalowanie

```bash
sudo ./integration/http-api/uninstall.sh
```

Usługi sensorów i ich dane pozostają nietknięte.
