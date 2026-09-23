# v1.1.1 — Quake-Catcher JoyWarrior Raspberry Pi standalone

**Release date:** 2026-09-18  
**Author / maintainer:** Marcin Kowalik <mkowalik@agh.edu.pl>  
**License:** MIT

## Highlights

- Updated the optional shared HTTP API to version 1.1.
- Preserves the latest valid Radioactive@Home CPM/dose when the current Radioactive row is reset/baseline, while keeping current status explicit.
- Adds provenance fields used by the shared sensor API.
- Keeps the validated RAM-first JoyWarrior24F14 acquisition/event pipeline unchanged.
- Keeps raw high-rate samples and active events in RAM.
- Keeps verified gzip + SHA-256 event commit, batched minute summaries, and retention controls.
- Keeps local control, diagnostics, and optional shared read-only sensor HTTP API.

## Hardware validated

- Code Mercenaries JoyWarrior24F14
- USB VID:PID 07c0:1116
- Raspberry Pi 3 Model B
- Raspberry Pi OS / Raspbian 13 Trixie 32-bit
