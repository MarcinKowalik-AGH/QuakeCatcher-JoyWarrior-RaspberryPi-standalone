# Quake-Catcher / JoyWarrior24F14 na Raspberry Pi — rejestrator RAM-first

**Wersja:** `1.1.0`  
**Autor:** **Marcin Kowalik**  
**E-mail:** **mkowalik@agh.edu.pl**  
**GitHub:** `MarcinKowalik-AGH`  
**Walidacja:** `2026-09-13`

Projekt zachowuje stary sensor Quake-Catcher / **Code Mercenaries JoyWarrior24F14** jako niezależny rejestrator drgań na Raspberry Pi. Pełny strumień ~111 Hz jest przetwarzany w RAM. Karta microSD nie otrzymuje ciągłego zapisu wysokiej częstotliwości. Pełny przebieg trafia na SD dopiero po wykryciu i zakończeniu zdarzenia, kompresji, sprawdzeniu gzip i obliczeniu SHA-256.

> Projekt zachowawczy / reverse-engineering: **Marcin Kowalik <mkowalik@agh.edu.pl>**.

## Zweryfikowany sensor

```text
VID:PID 07c0:1116
Code Mercenaries JoyWarrior24F14
serial testowanego egzemplarza: 000009F0
RAW HID: interfejs USB 1.0
raport: 7 bajtów
rzeczywista częstotliwość: ~111.11 Hz
```

Raport:

```text
X = bajty 0-1 uint16 LE
Y = bajty 2-3 uint16 LE
Z = bajty 4-5 uint16 LE
status = bajt 6
```

## Architektura RAM-first

```text
~111 Hz RAW HID
      |
      v
/run/qcn (RAM)
      |-- latest.json
      |-- baseline
      |-- bufor 30 s przed triggerem
      |-- aktywny event .part
      `-- minutowe summary oczekujące na flush

Po zakończeniu eventu:
gzip w RAM -> test -> liczba próbek -> SHA-256 -> dopiero zapis na SD
```

## Domyślne, zweryfikowane parametry

```text
trigger: 50 counts
potwierdzenie: 3 kolejne próbki
pre-trigger: 30 s
post-trigger: 60 s
max event: 600 s
kalibracja baseline: 10 s
summary: co 60 s
flush summary RAM -> SD: co 15 min
```

## Instalacja

```bash
git clone https://github.com/MarcinKowalik-AGH/QuakeCatcher-JoyWarrior-RaspberryPi-standalone.git
cd QuakeCatcher-JoyWarrior-RaspberryPi-standalone
sudo ./scripts/install.sh
qcnctl status
```

## Obsługa

```bash
qcnctl status
qcnctl live
qcnctl events
qcnctl latest-event
qcnctl verify-latest
qcnctl storage
qcnctl config
qcnctl threshold
sudo qcnctl threshold 50
sudo qcnctl prune
```

## Ochrona karty

- surowe 111 Hz: RAM;
- aktywny event: RAM;
- pełny event: SD dopiero po weryfikacji;
- summary: 1 rekord/min w RAM, zapis paczką co 15 min;
- katalog eventów: maks. 2 GiB;
- retencja eventów: 365 dni;
- utrzymywane minimum 4 GiB wolnego miejsca na `/`;
- journal systemowy ograniczony do 100 MiB / 1 miesiąca (opcjonalny plik w repo).

## Test produkcyjny

Zweryfikowany event miał 10 744 próbki, 131 075 bajtów po kompresji i SHA-256 `78d4141dbe2b7a62e065bb49b323405e4ff47965721a7b4b064a387322216862`. Plik został utworzony w RAM, przeszedł `gzip -t`, a dopiero potem został zapisany na SD. Po pełnym rebootcie usługa wstała automatycznie i wróciła do ~111,11 Hz.

## Opcjonalne lokalne HTTP API

Zweryfikowany moduł tylko-do-odczytu może wystawić bieżące dane obu sensorów w zaufanej sieci LAN:

```text
/sensors.json
/sensors.csv
/radioactive.json
/radioactive.csv
/qcn.json
/qcn.csv
/qcn/event/latest.json
```

Instaluje się go osobno, aby podstawowa instalacja sensora nie zajmowała automatycznie portu 80:

```bash
sudo ./integration/http-api/install.sh
```

API działa jako `www-data`, ma tylko `CAP_NET_BIND_SERVICE`, nie loguje każdego żądania i nie tworzy dodatkowego logu pomiarowego. Zostało zweryfikowane 13.09.2026 również z komputera macOS w LAN. Nie należy przekierowywać tego nieuwierzytelnionego portu bezpośrednio z Internetu.

Szczegóły: [`docs/pl/HTTP_API_PL.md`](docs/pl/HTTP_API_PL.md).

## Autor

**Marcin Kowalik**  
**mkowalik@agh.edu.pl**
