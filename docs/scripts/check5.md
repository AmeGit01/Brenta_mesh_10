# check5.py

Secondo passo (2026-11-17). Controllo indipendente della regola dei 5 m su un insieme di breakline: conta i vertici a distanza `(1 mm, 5 m)` da ogni incrocio sezione/breakline. Precedente: `fix5.py`.

## Requisiti

* Interprete: `python3` di Anaconda (shapely, numpy, scipy `cKDTree`).
* Cartella di lavoro corrente = `WD` (apre `secs_new.json` con percorso relativo).

## Input

* `secs_new.json` (`assemble.py`).
* Argomento 1: file JSON con la chiave `F` (fid → vertici), normalmente `fix5.json`; si usano le linee con almeno 2 vertici.

## Output

Solo stampa: `crossings <n> violations <k> [(sezione, distanza minima in m), ...]`.

## Parametri e costanti

* `5.0` m e `1e-3` m: finestra della regola.
* `1e-6` m: tolleranza per decidere se una breakline giace sulla sezione (entrambi gli estremi sulla sezione: 1225, 987) o se un vertice coincide con un altro incrocio della stessa sezione.

## Uso

```bash
cp scripts/check5.py /percorso/WD/
```

```bash
cd /percorso/WD
```

```bash
python3 check5.py fix5.json
```

(layout di `WD`: vedi [dpB.md](dpB.md), sezione Uso.)

## Funzionamento

Per ogni sezione: individua le breakline posate sulla sezione (escluse), calcola gli incroci con le altre (`P`), e per ogni incrocio cerca nel KD-tree dei vertici quelli entro 5 m, escludendo l'incrocio stesso (< 1 mm) e gli altri incroci della stessa sezione (nodi della sezione nei letti stretti). Ogni incrocio con almeno un vertice trovato è una violazione.

## Verifiche e limiti

* Atteso: 0 violazioni dopo `fix5.py`.
* Non controlla gli incroci nodestring/breakline (solo le sezioni) né la geometria complessiva (vedi `check_geom.py`).
