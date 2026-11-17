# cl2.py

Step 5. Liscia le centerline grezze, le ricampiona a esattamente 1 m (quindi **l'indice dell'array è la progressiva s in m**) e misura lungo la perpendicolare, in ogni punto, la distanza dal piede e dal ciglio delle sponde. Il risultato `cltab.pkl` è la centerline ufficiale usata da `widen.py`, `place.py` e `dump.py`. Segue `cl.py`, precede `chains.py`.

## Requisiti

* Python di Anaconda: numpy, scipy (`gaussian_filter1d`), shapely, matplotlib (`Agg`).
* Importa `core.py`: `load_graph`, `cls`, `boundary_segs`, `Rays`, `LineString`.

## Input

* `WD/work/graph.pkl` (via `load_graph`).
* `WD/work/rawcl.pkl` (`cl.py`): chiavi `main` e `vecchio` (array Nx2).

## Output

* `WD/work/cltab.pkl`: dict `{'main': {...}, 'vecchio': {...}}`; ciascuno con
  * `q` (Nx2): centerline lisciata, un punto ogni 1 m (indice = s);
  * `t` (Nx6): `[tl, tr, cl, cr, 0, 0]` distanze con segno dalla centerline: piede sul lato t<0 / t>0, ciglio sul lato t<0 / t>0 (m); NaN se la normale non incrocia le linee. Ultime due colonne sempre 0;
  * `B = tr - tl` larghezza del letto (piede-piede), `SL = tl - cl` e `SR = cr - tr` larghezza di sponda (piede-ciglio), `W = cr - cl` larghezza totale ciglio-ciglio (m).
* `WD/work/tab.png`: grafico delle larghezze di sponda (sopra, linea a 20 m) e di B e W (sotto, linea a 40 m).
* stdout per `main` e `vecchio`: lunghezza, punti senza incroci, percentili di B e delle sponde; poi, per blocchi di 3 km del main, percentili 1%/50% di B,SL,SR,W e frazione dove una sponda è < 10 m e < 20 m.

## Parametri e costanti

* Passo di ricampionamento 1.0 m (`res`, riga 8 e riga 34).
* Tangente locale: corda tra i punti `i-10` e `i+10` (`step=10`, riga 10).
* Raggio di ricerca ±1500 m.
* Lisciamento: Gaussiana sigma 6 (stretto) e sigma 60 (largo); peso del largo `a = clip((gauss(B,50) - 15)/35, 0, 1)`: 0 con letto <= 15 m, 1 con letto >= 50 m. Larghezza mancante sostituita con 10 m.
* Blocchi di report: 3000 m fino a 34 000 m (riga 43); soglie 10 e 20 m.

## Uso

```bash
python3 cl2.py /percorso/WD
```

## Funzionamento

1. `tb` = segmenti di piede (contorno delle facce `bed`), `tc` = segmenti di ciglio (contorno di `bed|sponda|muro`); oggetti `Rays` `Rb`, `Rc`.
2. Per ciascuna centerline: ricampiona a 1 m; prima tabella delle larghezze; liscia con il blend sopra; ricampiona a 1 m esatti; seconda tabella.
3. In `table(q)` la normale sinistra `n` di ogni punto è intersecata con piede e ciglio: `tl`/`cl` sono i colpi più vicini con t<0 (massimo), `tr`/`cr` quelli con t>0 (minimo).
4. Calcola `B,SL,SR,W`, stampa le statistiche, salva `cltab.pkl`, produce il grafico.

## Verifiche e limiti

* **Convenzione dei lati**: qui "L" (`tl`, `cl`, `SL`) indica il lato con t<0, cioè geometricamente il lato destro rispetto al verso della linea; in `widen.py` e `place.py` "L" è il lato con t>0. Nei report `SL`/`SR` sono quindi invertiti rispetto a `widen.py`; non ha effetto sul risultato perché da `cltab.pkl` gli altri script usano solo `q`.
* Il "ciglio" qui include anche i muri: in tratti urbani `SL`/`SR` piccoli sono normali.
* Il numero di punti di `q` coincide con la lunghezza in m: 33 981.6 m per l'asta e 3 058.7 m per il vecchio nel dataset finale.
* Punti con NaN in `t` (normale senza incroci) si hanno ai capi e in presenza di buchi nelle linee.
