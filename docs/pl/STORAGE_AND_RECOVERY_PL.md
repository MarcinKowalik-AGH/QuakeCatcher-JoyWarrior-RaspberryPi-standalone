# Pamięć masowa i odzyskiwanie — QCN

Autor: **Marcin Kowalik <mkowalik@agh.edu.pl>**

Dla karty ~16 GB zastosowano:

- eventy max 2 GiB;
- max wiek 365 dni;
- utrzymywanie co najmniej 4 GiB wolnego `/`;
- summary flush na SD co 15 min;
- summary rotowane miesięcznie, 24 kopie;
- journal max 100 MiB.

`/run/qcn` jest tmpfs i znika po rebootcie. To zamierzone. Pełne, zweryfikowane eventy pozostają w `/var/lib/qcn/events`.
