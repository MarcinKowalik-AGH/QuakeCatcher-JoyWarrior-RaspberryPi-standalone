# Instalacja — Quake-Catcher / JoyWarrior24F14

Autor: **Marcin Kowalik <mkowalik@agh.edu.pl>**

## Wymagania

Zweryfikowano na Raspberry Pi 3B z Raspberry Pi OS Lite 32-bit / Trixie. Sensor musi być widoczny jako `07c0:1116`.

```bash
lsusb | grep 07c0:1116
```

## Instalacja

```bash
git clone https://github.com/MarcinKowalik-AGH/QuakeCatcher-JoyWarrior-RaspberryPi-standalone.git
cd QuakeCatcher-JoyWarrior-RaspberryPi-standalone
sudo ./scripts/install.sh
```

Instalator robi backup bieżących plików do `/root/qcn-backup-*`, nie usuwa istniejących eventów ani summary, instaluje usługę RAM-first i timer retencji.

## Kontrola

```bash
qcnctl status
./scripts/healthcheck.sh
```

Po 10 s baseline powinien się ustalić; po minucie pojawi się pierwszy rekord w `/run/qcn/summary-live.csv`.

## Opcjonalne HTTP API

Po uruchomieniu sensora można opcjonalnie wykonać:

```bash
sudo ./integration/http-api/install.sh
```

Instalator nie nadpisuje innej usługi zajmującej TCP/80. Szczegóły: `docs/pl/HTTP_API_PL.md`.
