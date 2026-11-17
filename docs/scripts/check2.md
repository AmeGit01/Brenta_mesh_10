# check2.py

Verifica che boundary e breakline siano stati modificati solo dove previsto, che nessuna linea modificata ne incroci un'altra, e che le larghezze obiettivo siano raggiunte (a monte di Borgo: larghezza ciglio-ciglio ≥ 40 m; a valle: ciascuna sponda ≥ 16 m; Brenta vecchio: larghezza ≥ 40 m). Sta nel gruppo 19 dei controlli (dopo `write.py`). Solo stampa, righe etichettate A-H.

## Requisiti

* Interprete: `python3` di Anaconda.
* Pacchetti: numpy, shapely 2.x, geopandas, scipy (importato), `json`.
* Modulo importato: `core.py` (`Rays`, `boundary_segs`, `cls`, `SP`, `np`, `shapely`, `gpd`, `LineString`, `Point`).

## Input

Da `/home/amedeo/Documents/Brenta_mesh_10/layers/`: `breaklines_50m`, `breaklines` (originale), `boundary_50m`, `boundary` (originale), `regioni_ponti` (**originale**, non `_50m`), `centerline_50m`. `WD` serve solo per importare `core.py`.

## Output

Solo stampa (nessun file). Righe:

* **A**: boundary con geometria diversa dall'originale, `(fid, nome, massimo spostamento in m)`.
* **B**: numero di breakline con coordinate cambiate.
* **C**: numero e lista (prime 20) di coppie `(linea cambiata, altra)` che si incrociano (`crosses`); linee non semplici.
* **D**: numero di facce del grafo, di facce con almeno un punto regione.
* **E**: asta a monte di `s = 17335 m`: numero di campioni, W minimo / 1° percentile / mediana, campioni con W < 40 m e tratti `(s_inizio, s_fine, W_min)`.
* **F**: asta a valle: sponde SL/SR minimo e 1° percentile, numero di campioni con sponda < 16 m, tratti.
* **E2**: Brenta vecchio: W min/p1/mediana, campioni con W < 40 m, tratti.
* **G**: per ogni coppia di C, se anche l'originale si incrociava (`True` = preesistente).
* **H**: sezioni che intersecano esattamente 3 breakline, con i punti di intersezione.

## Parametri e costanti

* `17335` m: ascissa che separa monte e valle (fine di Borgo).
* `40` m: larghezza minima ciglio-ciglio (E, E2); `16` m: sponda minima a valle (F).
* `0.5` m: passo di campionamento lungo la centerline (da 1 m a lunghezza − 1 m); `±1 m` per la tangente.
* `1500` m: lunghezza dei raggi.
* Nomi di sezione riconosciuti: `S`/`V` + 5 cifre.

## Uso

```bash
python3 check2.py /percorso/WD
```

## Funzionamento

1. A-B: confronta boundary e breakline `_50m` con gli originali.
2. C-G: con uno `STRtree` cerca incroci propri tra le linee modificate e le altre, e controlla se esistevano già.
3. D-F: ricostruisce il grafo planare dai file su disco (breakline + boundary escluse le sezioni), assegna a ogni faccia il nome di un punto regione originale contenuto, estrae i contorni del letto `Rb` e di letto+sponda+muro `Rc`; campiona ogni 0.5 m la centerline, lancia raggi lungo la normale: `tl`/`tr` = distanze dei primi bordi di letto, `cl_`/`cr_` = distanze dei primi bordi di ciglio oltre il piede; `W = cl_ + cr_`, `SL = cl_ − tl`, `SR = cr_ − tr`.
4. H: elenca le sezioni che intersecano esattamente 3 breakline.

## Verifiche e limiti

* Criteri attesi (non asseriti dal codice): A = solo i boundary voluti; C vuoto o con coppie già preesistenti (G = `True`); E e E2 con 0 campioni sotto 40 m; F con 0 campioni sotto 16 m. Residui possono essere legittimi sulle sponde urbane/muri non spostati (`sponda_antro`, `muro`): confrontare i tratti stampati con quelle zone.
* Le facce sono nominate coi punti dell'**originale** `regioni_ponti.gpkg`: le facce che hanno solo punti nuovi non entrano nelle misure di larghezza (campioni NaN).
* Se un boundary modificato avesse un numero di vertici diverso dall'originale, la riga A fallirebbe (sottrazione di array di forma diversa).
* C'è una riga di codice morta (`gl=... if False else None`), innocua.
