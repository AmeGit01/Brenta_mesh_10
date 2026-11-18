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

## Secondo passo (17 novembre 2026): rami N/V/B e regola dei 5 m

Il 2026-11-17 le sezioni sono state rifatte in tre rami: **N** (asta principale da Caldonazzo a Borgo, fino a S16130 = N16050, `N00050`–`N16050`), **V** (primi 60 del Brenta vecchio, `V00050`–`V03000`) e **B** (Brenta a valle di Borgo, `B00000`–`B17650`, con B00050 almeno 5 m a monte di `Ponte_Bordignon_monte`), e la regola dei 5 m è stata applicata alle breakline. Gli script sono in `scripts/` (tranne `viol.py`, in `scripts/esplorativi/`).

Cartella di lavoro `WD`: `WD/in` (copie dei sei `layers/*_50m.gpkg`), `WD/in0` (copie degli originali `breaklines.gpkg`, `boundary.gpkg`, `regioni_ponti.gpkg`), `WD/work` (`core.py`, `next_bed.py`, `bank.py`, `cands.pkl`, `newfaces.pkl`, `dp.pkl`, `cltab.pkl` del lavoro del 2026-11-09, più `dpB.py`, `export_B.py`, `obst.py`), `WD/s16130/work` (esecuzione di `bank.py` per l'estensione di S16130), `WD/xn_points.json`. Gli script `assemble.py`, `fix5.py`, `check5.py`, `check_geom.py`, `regions2.py`, `prep_write.py` usano percorsi relativi e vanno lanciati con la cartella corrente = `WD`. Prima di `write2.py` i layer in `layers/` sono quelli del 2026-11-09; `write2.py` ne fa i backup datati `*_backup_20261117.gpkg`.

| # | Script | Cosa fa | Produce | Scheda |
|---|---|---|---|---|
| 0 | `prep_inputs_nvb.py` | prepara `xn_points.json`, la sezione fittizia del canale di destra della S16130 e l'elenco delle breakline dei muri da bloccare | `xn_points.json`, `s16130/work/sec_in.json`, `mat11_lines.json` | [prep_inputs_nvb.md](prep_inputs_nvb.md) |
| 1 | `dpB.py` | ricolloca il ramo B sui candidati dell'asta (programmazione dinamica) | `work/dpB.pkl` | [dpB.md](dpB.md) |
| 2 | `export_B.py` | dati delle sezioni B | `work/sec_in.json` | [export_B.md](export_B.md) |
| 3 | `next_bed.py` | limita la ricerca prima di un altro letto (invariato) | `sec_in.json` (aggiornato) | [next_bed.md](next_bed.md) |
| 4 | `obst.py` | limita la ricerca prima del primo ostacolo oltre il piede | `sec_in.json` (aggiornato) | [obst.md](obst.md) |
| 5 | `bank.py` (sistema, GDAL) | bankpoint sul DTM (invariato) | `work/bank_out.json` | [bank.md](bank.md) |
| 6 | `bank.py` in `s16130/` | bankpoint per l'estensione di S16130 | `s16130/work/bank_out.json` | [bank.md](bank.md) |
| 7 | `assemble.py` | sezioni N, V, B | `secs_new.json` | [assemble.md](assemble.md) |
| 8 | `fix5.py` | regola dei 5 m sulle breakline | `fix5.json` | [fix5.md](fix5.md) |
| 9 | `check5.py`, `check_geom.py` | verifiche su `fix5.json` | stampa | [check5.md](check5.md), [check_geom.md](check_geom.md) |
| 10 | `regions2.py` | un punto regione per faccia | `regions2.json` | [regions2.md](regions2.md) |
| 11 | `prep_write.py` | prepara le feature da scrivere | `write2.json` | [prep_write.md](prep_write.md) |
| 12 | `write2.py` (sistema, OGR) | backup datati e scrittura dei sei `layers/*_50m.gpkg` | `layers/*_50m.gpkg` | [write2.md](write2.md) |
| 13 | `verify2.py` | 24 controlli sui file riletti dal disco | stampa | [verify2.md](verify2.md) |

Esplorativo: [viol](esplorativi/viol.md) (conteggio delle violazioni dei 5 m sulle copie in `in/`).

Note: `xn_points.json` (punti di incontro nodestring/breakline) e `s16130/work/sec_in.json` sono prodotti da `prep_inputs_nvb.py` (passo 0). Il 17 novembre sono stati verificati identici a quelli usati per il lavoro.

## Terzo passo (18 novembre 2026): B00400 su idrometro_Borgo

Il 2026-11-18 tutto il ramo B è stato spostato verso monte di circa 16.6 m, perché la sezione B00400 coincida esattamente con la nodestring `idrometro_Borgo`. I rami N e V non cambiano. La cartella di lavoro è la stessa del secondo passo; `WD/in` contiene ancora le copie dei layer della mattina del 17 novembre, cioè i backup `*_backup_20261117.gpkg`.

| # | Script | Cosa fa | Produce | Scheda |
|---|---|---|---|---|
| 1 | `dpB2.py` | sposta il ramo B con la B00400 ancorata a `idrometro_Borgo` | `work/dpB2.pkl` | [dpB2.md](dpB2.md) |
| 2 | `export_B.py WD dpB2.pkl` | dati delle sezioni B, con la sezione ancorata | `work/sec_in.json` | [export_B.md](export_B.md) |
| 3–5 | `next_bed.py`, `obst.py`, `bank.py` | come nel secondo passo | `work/sec_in.json`, `work/bank_out.json` | |
| 6 | `assemble.py` | sezioni N, V, B; la B00400 diventa la nodestring | `secs_new.json` | [assemble.md](assemble.md) |
| 7–12 | `fix5.py`, `check5.py`, `check_geom.py`, `regions2.py`, `prep_write.py`, `write2.py`, `verify2.py` | come nel secondo passo | | |
| 13 | `sections_csv.py` | tabella delle sezioni | `docs/Brenta_sections_50m_mesh10.csv` | [sections_csv.md](sections_csv.md) |

Prima di `write2.py` lo stato corrente dei sei layer è stato copiato a mano in `*_backup_20261118.gpkg`, verificato con `cmp`. Poi i layer sono stati riportati ai backup del 17 mattina, perché `write2.py` applica le modifiche rispetto a quello stato; vedi [write2.md](write2.md).

## Quarto passo (18 novembre 2026): sezioni di Borgo sistemate a mano

L'utente ha modificato a mano in QGIS 11 sezioni B (B00000–B00550, tranne B00100) e `idrometro_Borgo` insieme alla B00400. Questi script riallineano gli altri layer, riparano gli effetti collaterali e controllano tutto. Si lanciano dalla cartella del progetto; `WD` serve solo per i file intermedi.

| # | Script | Cosa fa | Produce | Scheda |
|---|---|---|---|---|
| 1 | `sync_cp_bp.py` | linee d'asse, centerpoint e bankpoint dalle sezioni attuali | `WD/write3.json` | [sync_cp_bp.md](sync_cp_bp.md) |
| 2 | `write3.py` (sistema, OGR) | backup con etichetta e scrittura di un payload | `layers/*_50m.gpkg` | [write3.md](write3.md) |
| 3 | `fix_manual.py` | z = 0 delle sezioni, vertici a pochi mm dagli incroci, punti regione delle facce nuove | `WD/write3b.json` | [fix_manual.md](fix_manual.md) |
| 4 | `write3.py` (sistema, OGR) | scrive il payload di `fix_manual.py` | `layers/*_50m.gpkg` | [write3.md](write3.md) |
| 5 | `sync_cp_bp.py` | rilanciato come controllo: zero cambiamenti | | [sync_cp_bp.md](sync_cp_bp.md) |
| 6 | `verify3.py`, `verify3_dtm.py` (sistema) | controllo di tutti gli attributi, delle geometrie e delle regioni | stampa | [verify3.md](verify3.md), [verify3_dtm.md](verify3_dtm.md) |
| 7 | `sections_csv.py` | tabella delle sezioni | `docs/Brenta_sections_50m_mesh10.csv` | [sections_csv.md](sections_csv.md) |
| 8 | `dx_dev.py` | analisi di dx_dev tra sezioni consecutive | `docs/Brenta_dx_dev_50m.csv` | [dx_dev.md](dx_dev.md) |

Backup: `*_backup_20261118b.gpkg` (centerline, centerpoints, bankpoints, prima del passo 2) e `*_backup_20261118c.gpkg` (breaklines, boundary, regioni_ponti, prima del passo 4).
