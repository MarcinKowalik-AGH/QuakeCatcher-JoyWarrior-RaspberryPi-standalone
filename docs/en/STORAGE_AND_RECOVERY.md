# Storage and recovery — Quake-Catcher

Author: **Marcin Kowalik <mkowalik@agh.edu.pl>**

Active high-rate data and partial events live in tmpfs. Summary data is flushed in 15-minute batches. Persistent event retention is 2 GiB / 365 days, with a 4 GiB minimum free-space guard on `/`.
