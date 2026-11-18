# assemble.py

Secondo passo (2026-11-17), aggiornato il 2026-11-18 per la sezione ancorata. Costruisce `secs_new.json`, il nuovo insieme di sezioni in tre rami: **N** (asta principale fino a S16130, rinominata), **V** (primi 60 del Brenta vecchio), **B** (Brenta a valle di Borgo, da `dpB.py` e `bank.py`). Precedente: le esecuzioni di `bank.py`; successivo: `fix5.py`.

## Requisiti

* Interprete: `python3` di Anaconda (geopandas, shapely, numpy).
* Percorsi **relativi**: va eseguito con la cartella di lavoro corrente = `WD`.
* Non importa `core.py`.

## Input

* `in/boundary_50m.gpkg`, `in/bankpoints_50m.gpkg`, `in/centerpoints_50m.gpkg` (copie dei layer attuali).
* `work/sec_in.json` (sezioni B dopo `export_B.py`, `next_bed.py`, `obst.py`; dal 18 novembre il record di B00400 contiene la chiave `anchor`) e `work/bank_out.json` (`bank.py` sulle sezioni B).
* `s16130/work/sec_in.json` e `s16130/work/bank_out.json`: esecuzione di `bank.py` per estendere S16130; si usa il primo record (sezione) e il suo lato destro. Il file `sec_in.json` di questa cartella non è prodotto da nessuno script della pipeline (preparato a parte).
* `work/cands.pkl` e `work/dpB.pkl` sono caricati ma **non usati**.

## Output

* `WD/secs_new.json`: lista di dizionari `reach` (`N`/`V`/`B`), `old` (nome vecchio o `None`), `nome`, `s`, (`s_asta` per B), `cx`, `cy`, `coords` (2 vertici: sinistro, destro) e `sides` (due dizionari `sx`/`dx` con `x`, `y`, `z`, `dist_cp`, `tipo`, `regola`, `prom`, `moved`).
* Stampa conteggi per ramo, alcuni nomi (`secs[0]`, `secs[320]`, `secs[380]`, `secs[381]`, ultimo) e i bankpoint spostati a mano.

## Parametri e costanti

* Soglia `s_m <= 16130.01` per il ramo N; `iloc[:60]` per V.
* Nome: `f'{reach}{(k+1)*50:05d}'` per N e V (indice+1), `f'B{k*50:05d}'` per B (indice da 0).
* `secs[320]` deve essere `S16130` (assert): diventa N16050 ed è esteso a destra con `u = −(nx, ny)`, `t = XO['t']`.
* `moved`: distanza tra il vertice della sezione e il bankpoint del layer; `> 1e-6` significa spostato a mano (S00151/S01965); l'estensione di S16130 ha `moved = −1.0` (marcatore, non è "manuale").
* Regola dell'estensione: `regola='canale_dx'`, `tipo` = `kind` di `bank.py`.
* Sezione ancorata: `tipo='nodestring'`, `regola` = nome della nodestring (`idrometro_Borgo`), `z=None` (la quota la legge `write2.py` dal DTM), `prom=None`, `moved=0`.

## Uso

```bash
cp scripts/assemble.py /percorso/WD/
```

```bash
cd /percorso/WD
```

```bash
python3 assemble.py
```

(layout di `WD`: vedi [dpB.md](dpB.md), sezione Uso.)

## Funzionamento

1. Carica i layer di `in/`, ordina i centerpoint `main` e `vecchio` per `s_m`.
2. Per N e V: per ogni centerpoint legge i due vertici della sezione dal layer boundary (nome vecchio) e i due bankpoint (`<nome>_sx`, `<nome>_dx`) e calcola `moved`.
3. Estende l'ultima sezione N (S16130) al canale destro con il bankpoint calcolato da `bank.py` in `s16130/`.
4. Per B: per ogni sezione di `sec_in.json` con tag `B` calcola i due vertici `centro ± n·t` da `bank_out.json`; `s` è relativa alla prima sezione B (`s_asta` mantiene la progressiva dell'asta). Se il record ha la chiave `anchor`, la sezione diventa la nodestring stessa: vertici della nodestring (sinistro per primo), centro nell'intersezione con la linea d'asse, progressiva di quel punto. Il risultato di `bank.py` per quella sezione viene ignorato e lo script stampa `anchor section B00400 = idrometro_Borgo`.
5. Stampa il riepilogo e salva `secs_new.json`.

## Verifiche e limiti

* Atteso: 735 sezioni (N 321, V 60, B 354; il 18 novembre N e V sono risultate identiche a quelle del 17); controllare i nomi stampati (N00050, N16050, V00050, V03000, B17650) e che solo S00151/S01965 compaiano tra i bankpoint spostati a mano.
* L'indice `320` è fisso: se cambia il numero di sezioni N, l'assert si rompe.
* `sec_in.json` e `bank_out.json` della cartella `work/` devono essere quelli del ramo B (non del 2026-11-09).
* `bp[bp.nome==nm].iloc[0]` fallisce se manca un bankpoint di una sezione vecchia.
