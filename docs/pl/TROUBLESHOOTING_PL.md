# Diagnostyka — Quake-Catcher

Autor: **Marcin Kowalik <mkowalik@agh.edu.pl>**

## Brak sensora

```bash
lsusb | grep 07c0:1116
for H in /sys/class/hidraw/hidraw*; do cat "$H/device/uevent" 2>/dev/null | grep -E 'HID_ID|HID_NAME'; done
```

## Usługa

```bash
systemctl status qcn-recorder.service
journalctl -u qcn-recorder.service -n 100
qcnctl live
```

## Weryfikacja ostatniego eventu

```bash
qcnctl verify-latest
```

## Gdy eventów jest za dużo

```bash
sudo qcnctl prune
```
