# q.py

Script esplorativo (non necessario per produrre i layer). Interrogazione ad hoc: stampa nome, `mat_id` e prima coordinata di alcuni punti regione e, per alcune breakline, estremi, numero di vertici e se sono state spostate. Fid scritti a mano per un'indagine del 2026-11-09. Dopo `apply_widen.py` (passo 8).

## Requisiti

`python3` di Anaconda; importa `core.py` da `WD/work`.

## Input

* `WD/in/regioni_ponti.gpkg` (campi `nome`, `mat_id`, geometria).
* `WD/work/chains.pkl` (`chains.py`): `feat`.
* `WD/work/widen2.pkl` (`apply_widen.py`): `newf`.

## Output

Solo stampa: per i punti regione `fid nome mat_id (x, y)`; per le breakline `fid primo_vertice ultimo_vertice n <numero vertici> [moved]`.

## Parametri e costanti

* Fid dei punti regione: `89, 114, 81, 90, 116, 57, 58`.
* Fid delle breakline: `1394, 1405, 1412, 1423, 979, 1001, 1061, 1002`.
Modificabili direttamente nelle due liste.

## Uso

```bash
python3 q.py /percorso/WD
```

## Funzionamento

Legge i punti regione e stampa gli attributi richiesti; poi per ciascuna breakline stampa le coordinate (arrotondate a 0.1 m) del primo e ultimo vertice, `n` vertici, e `moved` se il fid è in `newf`.

## Verifiche e limiti

Valido solo con quei fid; un fid assente solleva `KeyError`. Nessun file scritto.
