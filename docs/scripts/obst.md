# obst.py

Secondo passo (2026-11-17). Limita la ricerca dei bankpoint (campi `maxL`/`maxR` di `sec_in.json`) a 0.5 m prima del primo ostacolo oltre il piede: nodestring non-sezione, breakline interne (segmenti né di piede né di ciglio) e il piede di un altro letto. Ricostruisce il passo di limitazione del 2026-11-09 che non era stato salvato. Precedente: `next_bed.py`; successivo: `bank.py`.

## Requisiti

* Interprete: `python3` di Anaconda; `core.py` da `WD/work` (`SP`, `cls`, `boundary_segs`, `ring_segs`, `key`, `Rays`, `gpd`, `shapely`, `np`); `json`.
* Lo script va copiato in `WD/work`.

## Input

* `WD/work/newfaces.pkl` (`place.py`): `fc` (facce dopo l'allargamento) e `rows`.
* `WD/work/sec_in.json` (`export_B.py`, poi `next_bed.py`).
* Argomento 2: percorso di `boundary.gpkg` (nel lavoro finale `WD/in0/boundary.gpkg`, il file originale); dei suoi oggetti si usano quelli il cui nome **non** è `[S|V|N|B]` + 5 cifre.

## Output

* `WD/work/sec_in.json` sovrascritto con `maxL`/`maxR` abbassati dove serve (un limite viene solo abbassato, mai alzato).
* Stampa ogni limite (` obstacle cap <iniziale> <progressiva> <chiave> <valore> toe <piede>`) e il totale `obstacle caps N`.

## Parametri e costanti

* `0.5` m: il limite sta 0.5 m prima dell'ostacolo (`lim = v[0] − 0.5`).
* `1500` m: lunghezza massima dei raggi.
* `0.5` m (a monte del piede), `1e-6`: un ostacolo conta se la sua distanza è in `(piede − 0.5, ciglio − 1e-6)`.
* `0.05` m: un piede di un altro letto conta se è oltre il proprio piede di più di 5 cm.
* Classi di faccia: `'bed'` per i piedi, `'bed'/'sponda'/'muro'` per piedi e cigli.

## Uso

```bash
cp scripts/obst.py /percorso/WD/work/
```

```bash
python3 /percorso/WD/work/obst.py /percorso/WD /percorso/WD/in0/boundary.gpkg
```

(layout di `WD`: vedi [dpB.md](dpB.md), sezione Uso.)

## Funzionamento

1. `tb`: segmenti di confine dei letti (piedi); `tc`: segmenti di confine di letto, sponda e muro; `skip` = chiavi dei segmenti di `tb` e `tc`.
2. `inner`: segmenti unici degli anelli delle facce non presenti in `skip` (breakline interne). `nseg`: segmenti delle nodestring non-sezione di `boundary.gpkg`.
3. `R` = raggi contro `inner` + `nseg`; `RB` = raggi contro i piedi (`tb`).
4. Per ogni sezione e lato (`+1` sinistra → `maxL`, `−1` destra → `maxR`) raccoglie le distanze di `R` nell'intervallo valido e quelle di `RB` oltre il proprio piede; se ce n'è almeno una pone il limite 0.5 m prima della più vicina, se è minore di quello esistente.
5. Riscrive `sec_in.json`.

## Verifiche e limiti

* Idempotente.
* La stampa elenca i limiti applicati: controllarli rispetto a ponti e rami laterali.
* Il filtro sui nomi delle nodestring (`[SVNB]` + 5 cifre) esclude le sezioni; una nodestring con un nome di questo tipo verrebbe ignorata.
* Dipende dalle facce di `newfaces.pkl` (stato del 2026-11-09), non dai breakline modificati da `fix5.py`.
