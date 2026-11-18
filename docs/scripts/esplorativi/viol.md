# viol.py

Script esplorativo (non necessario per produrre i layer). Conta le violazioni della regola dei 5 m (vertice di breakline a distanza `(1 mm, 5 m)` da un incrocio sezione/breakline) su un insieme di layer `*_50m`. Usato nel secondo passo (2026-11-17), in particolare sulle copie in `WD/in`.

## Requisiti

* Interprete: `python3` di Anaconda (geopandas, shapely, numpy, scipy `cKDTree`).
* Percorsi relativi: cartella corrente = `WD` se si usa la cartella predefinita `in`.

## Input

* Argomento 1 (opzionale, predefinito `in`): cartella con `breaklines_50m.gpkg` e `boundary_50m.gpkg`.
* Opzione `-v`: elenca ogni violazione.

## Output

Solo stampa: `crossings <n> viol <k> sections <s> <0.5 <m>` (incroci, violazioni, sezioni coinvolte, violazioni a meno di 0.5 m); con `-v` le tuple `(sezione, fid breakline, distanza, (x, y))`.

## Parametri e costanti

* `5.0` m e `1e-3` m: finestra della regola; `0.5` m: soglia dell'ultimo conteggio.
* Sezione = nome `[S|V|N|B]` + 5 cifre.

## Uso

```bash
cd /percorso/WD
```

```bash
python3 /percorso/scripts/esplorativi/viol.py in
```

```bash
python3 /percorso/scripts/esplorativi/viol.py in -v
```

## Funzionamento

Costruisce l'indice delle breakline e il KD-tree dei vertici; per ogni sezione e ogni incrocio con una breakline raccoglie i vertici entro 5 m (distanza > 1 mm) e registra la distanza minima.

## Verifiche e limiti

* A differenza di `check5.py` non esclude le breakline posate su una sezione né gli altri incroci della stessa sezione: dà quindi un conteggio più severo (sovrastima nei letti stretti).
* Il primo argomento è sempre la cartella; `-v` è riconosciuto in qualunque posizione, ma se è il primo argomento viene letto come cartella.
