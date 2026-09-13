# Kalibracja i trigger — Quake-Catcher

Autor: **Marcin Kowalik <mkowalik@agh.edu.pl>**

Testowany egzemplarz w spoczynku miał std około 2,9-3,7 counts i `max_step` około 7-10 counts. Kontrolowane poruszenie/stuknięcie generowało wartości setki lub tysiące counts. Dlatego startowy próg produkcyjny ustawiono na 50 counts przez 3 kolejne próbki.

To jest próg eksploatacyjny dla konkretnego stanowiska testowego, nie uniwersalny próg sejsmologiczny. Po zmianie miejsca montażu należy obserwować `summary.csv` i ewentualnie skorygować:

```bash
sudo qcnctl threshold 50
```
