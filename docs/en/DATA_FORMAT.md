# Data format — Quake-Catcher

Author: **Marcin Kowalik <mkowalik@agh.edu.pl>**

Raw HID is 7 bytes: X/Y/Z as little-endian uint16 and one status byte. Persistent summaries contain one-minute statistics. Event payloads are gzip CSV with UTC/ns timestamps and X/Y/Z/status; JSON metadata includes integrity and trigger information.
