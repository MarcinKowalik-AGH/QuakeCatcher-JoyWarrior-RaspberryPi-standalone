# Troubleshooting — Quake-Catcher

Author: **Marcin Kowalik <mkowalik@agh.edu.pl>**

Check `lsusb | grep 07c0:1116`, `systemctl status qcn-recorder.service`, `journalctl -u qcn-recorder.service`, and `qcnctl live`. Verify the latest event with `qcnctl verify-latest`.
