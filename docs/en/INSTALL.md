# Installation — Quake-Catcher / JoyWarrior24F14

Author: **Marcin Kowalik <mkowalik@agh.edu.pl>**

```bash
git clone https://github.com/MarcinKowalik-AGH/QuakeCatcher-JoyWarrior-RaspberryPi-standalone.git
cd QuakeCatcher-JoyWarrior-RaspberryPi-standalone
sudo ./scripts/install.sh
qcnctl status
```

Validated device: `07c0:1116`. The installer preserves existing event/summary data and backs up replaced configuration.

## Optional HTTP API

After the sensor itself is working, optionally run:

```bash
sudo ./integration/http-api/install.sh
```

The installer refuses to replace another service already using TCP/80. See `docs/en/HTTP_API.md`.
