# prep_inputs_nvb.py

Prepara i due file d'ingresso del secondo passo (17 novembre 2026, rami N/V/B) che non vengono prodotti da altri script:

* `WD/xn_points.json`: i punti in cui una nodestring che non è una sezione incontra una breakline. `dpB.py` li usa per penalizzare le sezioni del ramo B il cui piede cade a meno di 5 m da uno di questi punti;
* `WD/s16130/work/sec_in.json`: una sezione fittizia centrata nel canale di destra attraversato dalla S16130 (la futura N16050). Serve a `bank.py` per cercare il nuovo bankpoint destro quando la sezione viene allungata fino a quel canale.

Produce inoltre `WD/mat11_lines.json`: l'elenco delle breakline che delimitano le strisce di muro (regioni con `mat_id` 11). `fix5.py` deve lasciarle esattamente come sono.

Va lanciato per primo, prima di `dpB.py`. Il passo successivo che usa il secondo file è l'esecuzione di `bank.py` nella cartella `s16130/`.

## Requisiti

* Python di Anaconda (`python3`) con geopandas, shapely e numpy.
* Nessun altro script del progetto.

## Input

* `WD/in/breaklines_50m.gpkg`: copia delle breakline prima dell'aggiornamento N/V/B. Servono le linee 970, 853, 1129 e 949 attorno alla S16130.
* `WD/in/boundary_50m.gpkg`: copia delle nodestring prima dell'aggiornamento, che contiene ancora la vecchia sezione `S16130`. Le sezioni vecchie si riconoscono dal nome: `S` o `V` seguita da cinque cifre.

## Output

* `WD/xn_points.json`: elenco di coppie `[x, y]`. Sono le intersezioni di ogni nodestring non di sezione con l'unione delle breakline, comprese le estremità dei tratti in cui le due linee si sovrappongono. Il 17 novembre i punti erano 197.
* `WD/s16130/work/sec_in.json`: lista con un solo elemento, nel formato di `bank.py`. I campi sono `stream`, `s`, `x`, `y` (centro del canale di destra), `nx`, `ny` (normale rivolta a sinistra, quindi il lato R guarda verso la sponda destra), `tL`, `tR`, `cL`, `cR` e `maxR`. `tL` e `tR` sono la mezza larghezza del canale. `cL` e `cR` sono la distanza dal ciglio, cioè la linea 949. `maxR` è il limite di ricerca, 0.5 m prima della striscia di muro 1129.

* `WD/mat11_lines.json`: lista dei fid delle breakline che condividono più di 1 cm con il contorno di una faccia di muro. Il 17 novembre erano 32: 893, 910–913, 915, 916, 918, 972, 1062, 1063, 1068–1071, 1125–1133 e 1135–1142.

Per l'elenco delle linee bloccate serve anche `WD/in/regioni_ponti_50m.gpkg`, per trovare i punti con `mat_id` 11.

## Parametri e costanti

| Costante | Valore | Significato |
|---|---|---|
| sezione | `S16130` | sezione da allungare, cercata per nome in `boundary_50m` |
| prolungamento | 60 m | lunghezza della retta della sezione verso destra su cui si cercano gli incroci |
| 970 | 2° incrocio (14.717 m) | bordo destro dell'isola tra i due canali, cioè il piede sinistro del canale di destra |
| 853 | 20.263 m | piede destro del canale di destra |
| 1129 | 28.133 m | prima linea della striscia di muro dentro la sponda urbana |
| 949 | 41.19 m | ciglio della sponda urbana |
| margine | 0.5 m | distanza minima dall'ostacolo (regola dei bankpoint) |

Le distanze sono misurate lungo la retta della sezione a partire dal suo estremo sinistro e arrotondate al millimetro, come nel calcolo originale. I numeri delle breakline sono fissi nel codice: valgono solo per questa sezione e per questi dati.

## Uso

Preparare la cartella di lavoro con le copie dei layer:

```bash
mkdir -p WD/in
```

```bash
cp layers/breaklines_50m.gpkg layers/boundary_50m.gpkg WD/in/
```

Lanciare lo script:

```bash
python3 scripts/prep_inputs_nvb.py WD
```

Poi calcolare il bankpoint destro della S16130 allungata:

```bash
cp scripts/bank.py WD/s16130/work/
```

```bash
/usr/bin/python3 WD/s16130/work/bank.py WD/s16130
```

## Funzionamento

1. Unisce tutte le breakline non vuote in un'unica geometria.
2. Per ogni nodestring che non è una sezione, calcola l'intersezione con quell'unione e ne salva le coordinate in `xn_points.json`.
3. Prende la vecchia S16130 e la prolunga di 60 m verso destra, partendo dall'estremo sinistro.
4. Lungo questa retta misura dove incrocia le linee 970, 853, 1129 e 949.
5. Costruisce una sezione fittizia centrata nel canale di destra, con piedi, ciglio e limite di ricerca presi da quegli incroci. `bank.py` cercherà il bankpoint dal piede destro verso l'esterno e si fermerà 0.5 m prima del muro.
6. Ricostruisce il grafo planare di breakline e nodestring, senza sezioni, e trova le facce che contengono un punto regione con `mat_id` 11, cioè le strisce di muro (19 facce). Salva i fid delle breakline che ne formano il contorno, anche solo per un tratto più lungo di 1 cm.

## Verifiche e limiti

* Il 17 novembre i due file prodotti sono risultati identici a quelli usati per il lavoro.
* Lo script funziona solo sui layer **precedenti** all'aggiornamento N/V/B. Dopo l'aggiornamento la `S16130` non esiste più (si chiama `N16050`) e le breakline sono state modificate.
* Gli identificativi delle linee (970, 853, 1129, 949) sono stati scelti guardando la mappa. Se i dati cambiano, vanno ricontrollati.
* Con le nuove sezioni (`N`, `V`, `B`) il filtro sul nome non le riconoscerebbe come sezioni: vale solo per i nomi vecchi `S` e `V`.
