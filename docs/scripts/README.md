# Script delle sezioni a 50 m – indice

Gli script si trovano in `scripts/` (pipeline e verifiche) e `scripts/esplorativi/` (ispezioni e grafici). Hanno prodotto il 2026-11-09 i file `layers/*_50m.gpkg`.
Ogni script ha una scheda in questa cartella, con requisiti, input, output, parametri, uso, funzionamento, verifiche e limiti, e commenti in inglese nel codice. Il registro completo del lavoro è in [`docs/workflow.md`](../workflow.md); regole e metodo in [`docs/Brenta_regole_e_metodo.md`](../Brenta_regole_e_metodo.md).

## Ambiente

* Quasi tutti: Python di Anaconda (`python3`) con geopandas, shapely 2.1, numpy, scipy, networkx, matplotlib.
* `bank.py` e `write.py` (e `check_bp.py`): `/usr/bin/python3` di sistema, che ha GDAL/OGR.

## Cartella di lavoro

Ogni script riceve come unico argomento una cartella di lavoro `WD`, con:

* `WD/in/`: copie di `breaklines.gpkg`, `boundary.gpkg`, `regioni_ponti.gpkg` da `layers/`;
* `WD/work/`: gli script di `scripts/` (gli altri importano `core.py` da `WD/work`) e i risultati intermedi (`.pkl`, `.json`).

Preparazione:

```bash
mkdir -p WD/in WD/work
```

```bash
cp layers/breaklines.gpkg layers/boundary.gpkg layers/regioni_ponti.gpkg WD/in/
```

```bash
cp scripts/*.py WD/work/
```

Il DTM viene letto direttamente da `layers/DTM_finale.tif`. Solo `write.py` scrive in `layers/`, e solo i file `_50m`. Se uno di questi esiste già si ferma (`exists: <nome>`), quindi per rigenerarli vanno prima cancellati a mano. Non crea backup; gli originali di `layers/` non vengono toccati.

## Ordine di esecuzione

L'ordine è ricostruito dai file intermedi che ogni script legge e scrive. Gli script non sono stati rieseguiti da zero dopo la copia.

| # | Script | Cosa fa | Produce | Scheda |
|---|---|---|---|---|
| – | `core.py` | funzioni comuni (classi delle facce, raggi, grafo) | – | [core.md](core.md) |
| 1 | `graph.py` | grafo planare di breakline + boundary, facce e classi | `graph.pkl` | [graph.md](graph.md) |
| 2 | `skel.py` | scheletro di Voronoi del bed | `skel.pkl` | [skel.md](skel.md) |
| 3 | `net.py` | rete dello scheletro (solo diagnostica, letta da `esplorativi/stats.py`) | `net.pkl` | [net.md](net.md) |
| 4 | `cl.py` | centerline grezze di asta e Brenta vecchio | `rawcl.pkl`, `altmain.pkl` | [cl.md](cl.md) |
| 5 | `cl2.py` | centerline lisciate e progressive | `cltab.pkl` | [cl2.md](cl2.md) |
| 6 | `chains.py` | catene dei cigli da spostare | `chains.pkl` | [chains.md](chains.md) |
| 7 | `widen.py` | allargamento (40 m a monte di Borgo, 16 m per sponda a valle) | `widen.pkl` | [widen.md](widen.md) |
| 8 | `apply_widen.py` | applica l'allargamento alle breakline | `widen2.pkl`, `bgn.pkl`, `widen_faces.pkl` | [apply_widen.md](apply_widen.md) |
| 9 | `gaps.py` | controllo dei residui di larghezza (solo stampa) | – | [gaps.md](gaps.md) |
| 10 | `place.py` | candidati per le sezioni ogni 0.25 m | `cands.pkl`, `newfaces.pkl` | [place.md](place.md) |
| 11 | `dp.py` | programmazione dinamica: sezioni a 50 ± 0.5 m | `dp.pkl` | [dp.md](dp.md) |
| 12 | `export_sec.py` | dati delle sezioni per il calcolo dei bankpoint | `sec_in.json` | [export_sec.md](export_sec.md) |
| 13 | `next_bed.py` | limita la ricerca prima di un altro letto | `sec_in.json` (aggiornato) | [next_bed.md](next_bed.md) |
| 14 | `bank.py` | bankpoint sul DTM (sistema, GDAL) | `bank_out.json` | [bank.md](bank.md) |
| 15 | `finals.py` | sezioni finali a 2 vertici | `secs0.pkl` | [finals.md](finals.md) |
| 16 | `regions.py` | nuovi punti regione | `finalfaces.pkl`, `regions.json` | [regions.md](regions.md) |
| 17 | `dump.py` | prepara le feature da scrivere | `write.json` | [dump.md](dump.md) |
| 18 | `write.py` | scrive i file `_50m` in `layers/` (sistema, OGR) | `layers/*_50m.gpkg` | [write.md](write.md) |
| 19 | `check.py`, `check2.py`, `check_bp.py`, `final.py` | verifiche sui file riletti dal disco | stampa, CSV | [check.md](check.md), [check2.md](check2.md), [check_bp.md](check_bp.md), [final.md](final.md) |

## Script esplorativi

Non servono a produrre i file; sono stati usati per ispezioni, grafici e prove: [bq](esplorativi/bq.md), [inspect1](esplorativi/inspect1.md), [map](esplorativi/map.md), [plotcl](esplorativi/plotcl.md), [q](esplorativi/q.md), [stats](esplorativi/stats.md), [up](esplorativi/up.md), [zoom](esplorativi/zoom.md).

## Anomalie note nel codice (non corrette)

Le ho lasciate così perché correggerle cambierebbe la riproduzione dei file già consegnati e verificati.

* `place.py`: per il lato sinistro l'estensione provvisoria del segmento usato nei controlli di incrocio testa `tL+cR>30` invece di `tL+tR>30`. Riguarda solo la scelta dei candidati, non i bankpoint, la cui regola dei 30 m è in `bank.py`. Le sezioni finali hanno superato il controllo sugli incroci.
* `cl2.py`: chiama "L" il lato opposto rispetto a `widen.py`/`place.py` nei campi `SL`/`SR` di `cltab.pkl`. Questi campi non sono usati a valle.
* `final.py`: si interrompe con un errore se non c'è nessuna violazione della regola dei 5 m. La soglia `index>176` per i nuovi punti regione è fissa nel codice.
* `check_bp.py`: non gestisce bankpoint con `z_dtm` nullo, che finora non si sono verificati.
* `check2.py`: legge i nomi delle facce dal `regioni_ponti` originale, quindi le facce con soli punti nuovi danno larghezza NaN.
* `finals.py`: l'elenco degli incroci con i cigli include i bordi del bed, quindi è poco informativo.
* Codice inutilizzato in `place.py`, `widen.py`, `net.py`, `cl.py`, `chains.py` e `dp.py`, indicato nelle schede.
