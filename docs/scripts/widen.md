# widen.py

Step 7. Calcola di quanto va spostato verso l'esterno ogni ciglio (top-of-bank) per ottenere la larghezza voluta e genera la nuova geometria delle feature spostate. Regola: a monte di Borgo (`s <= BORGO_END = 17 335 m` sull'asta) e sul Brenta vecchio la larghezza totale ciglio-ciglio deve essere >= 40.10 m (spostamento simmetrico); a valle di Borgo ogni sponda (piede-ciglio) deve essere >= 16.05 m. Gli spostamenti sono limitati per lasciare >= 5 m dalla linea esterna successiva; le sponde antropiche (`sponda_antro`) e i muri non si muovono. Segue `chains.py`, precede `apply_widen.py`.

## Requisiti

* Python di Anaconda: numpy, scipy (`cKDTree`), shapely 2.1, geopandas.
* Importa `core.py`: `load_graph`, `cls`, `boundary_segs`, `Rays`, `collections`, `Point`, `LineString`, ecc.

## Input

* `WD/work/graph.pkl` (via `load_graph`): facce e nomi.
* `WD/work/chains.pkl` (`chains.py`): `feat`, `S`, `meta`, `L`, `R`, `Lc`, `Rc`, `istop`.
* `WD/work/cltab.pkl` (`cl2.py`): solo `T0[name]['q']`, la centerline a 1 m.
* `WD/in/boundary.gpkg`: geometrie delle linee di boundary (`fid_as_index=True`) e campo `nome` (solo per i messaggi).

## Output

* `WD/work/widen.pkl`: dict con
  * `newf`: `fid -> array Nx2` della nuova geometria delle sole feature "top" effettivamente spostate;
  * `bmove`: `tag -> nuova posizione (xy)` dei vertici "forzati", con `tag = ('bl', fid, estremo)` per estremi di altre breakline e `('bd', fid_boundary, estremo)` per estremi di boundary;
  * `endT`: `(x,y) originale arrotondato al mm -> nuovo xy` per gli stessi punti;
  * `bgeo`: `fid boundary -> vertici originali`;
  * `ST`: `(nm, D)`: nomi (`main`/`vecchio`) e matrice con colonne `i, x, y, nx, ny, tL, tR, cL, cR, W, oL, oR` per ogni punto della centerline con incroci validi;
  * `sL`, `sR`: spostamento sinistro/destro (m) per riga di `D`;
  * `PTS` (punti sul ciglio, due per stazione), `SH` (spostamento in m), `DN` (direzione unitaria verso l'esterno).
  Letto da `apply_widen.py`.
* stdout: numero di punti limitati dal vincolo dei 5 m, frazione di punti allargati per lato e massimo, statistiche a valle di Borgo (frazione, km, massimo), numero totale di feature top, "boundary end coincident w breakline: left as is", "boundary end at chain vertex", numero di punti forzati, "mixed skip <fid>", numero di feature cambiate.

## Parametri e costanti

* `BORGO_END = 17335.` m (riga 10): fine del tratto urbano di Borgo sull'asta.
* `40.10` m: larghezza minima ciglio-ciglio a monte e sul vecchio (riga 30).
* `16.05` m: larghezza minima piede-ciglio per sponda a valle (riga 28).
* `5` m: distanza minima dalla linea esterna successiva (righe 36-37).
* Raggio dei raggi ±1500 m.
* `3.0` m: distanza massima di una stazione dal vertice per applicarne lo spostamento (`shift_at`, riga 54).
* Densificazione dei cigli a 2 m; semplificazione 0.02 m e rimozione dei vertici più vicini di 2 m (righe 100, 117, 120).
* Tolleranze: `1e-3` m (contatti), `1e-6` (confronti), spostamento minimo applicato 1e-3 m; `c>0.5` per la proiezione lungo la direzione della linea incidente (riga 111).

## Uso

```bash
python3 widen.py /percorso/WD
```

## Funzionamento

1. Carica dati; `tb` (piede: bed), `tc` (ciglio: bed|sponda|muro), `to` (anche `inter`) con oggetti `Rays`.
2. Per ogni punto della centerline di `main` e `vecchio`: normale sinistra, colpi su piede/ciglio/"esterno"; calcola `tL,tR` (centerline-piede), `cL,cR` (centerline-ciglio oltre il piede), `W = cL+cR`, `oL,oR` (prossima linea esterna oltre il ciglio). Lato L = t>0 (sinistro), R = t<0.
3. Regola di spostamento `rule` (vedi sopra); poi tetto `min(shift, max(gap-5, 0))` con `gap = o - c`.
4. Stazioni sul ciglio `TL = centro + n·cL`, `TR = centro - n·cR` con spostamento e direzione; `KD-tree` per assegnare lo spostamento a un punto qualunque (entro 3 m).
5. `topfid`: segmenti ciglio per feature; `ALL` = feature con almeno un segmento ciglio.
6. Punti "forzati": estremi di altre breakline (`bl`) e delle boundary (`bd`) che cadono su un ciglio (giunzioni a T), da conservare e spostare con esso.
7. Per ogni feature in `ALL` (esclusa se tocca `sponda_antro`, o se è mista: stampa `mixed skip`): densifica a 2 m più vertici originali e punti forzati, sposta i punti, per i vertici forzati sposta lungo la direzione `u` della linea incidente (`P + u·sh/c`) o, se l'angolo è troppo obliquo, lungo la normale; spezza ai vertici forzati, semplifica e dirada; ricompone in `newf`.
8. Registra le nuove posizioni dei punti forzati in `endT` e `bmove`; salva `widen.pkl`.

## Verifiche e limiti

* Le feature miste (parte ciglio, parte no) e quelle che toccano `sponda_antro` restano invariate.
* `spondaname()` è definita ma mai usata.
* Se la normale non incrocia piede/ciglio da un lato la stazione è esclusa (nessuno spostamento lì).
* Dopo l'esecuzione controllare "clamped by clearance" (numero elevato = poco spazio), le percentuali di allargamento e il numero di `mixed skip`.
* La nuova geometria è validata solo da `apply_widen.py`.
