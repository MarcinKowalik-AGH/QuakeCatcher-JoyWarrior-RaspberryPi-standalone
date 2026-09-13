# Operations — Quake-Catcher

Author: **Marcin Kowalik <mkowalik@agh.edu.pl>**

High-rate acquisition stays in RAM. Completed events are verified and hashed before SD commit. Use `qcnctl status`, `qcnctl live`, `qcnctl events`, `qcnctl verify-latest`, `qcnctl storage`, and `sudo qcnctl threshold <value>`.

## HTTP API status

If the optional API is installed:

```bash
systemctl status sensor-http-api.service --no-pager
curl -s http://127.0.0.1/sensors.json | python3 -m json.tool
```
