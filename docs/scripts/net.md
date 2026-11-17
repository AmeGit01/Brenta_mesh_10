# net.py

Step 3. Dallo scheletro estrae i cammini minimi dalla boundary `BC_caldonazzo` (monte) a `BC_brenta_valle` (valle) e da ogni altra boundary `BC_*` verso il cammino principale (affluenti), li liscia e calcola le larghezze di bed e corridoio. Segue `skel.py`, precede `cl.py` nell'ordine ricostruito. Lo script è in pratica diagnostico/esplorativo: `net.pkl` non è letto da altri script della cartella `scripts/` (solo da `esplorativi/stats.py`) e `cl.py` ricostruisce le centerline per conto suo.

## Requisiti

* Python di Anaconda: geopandas, shapely, numpy, scipy (`gaussian_filter1d`), networkx, matplotlib (backend `Agg`).
* Non importa `core.py`.

## Input

* `WD/work/skel.pkl` (`skel.py`): `g`, `vv`, `bed`, `cor`.
* `WD/in/boundary.gpkg`: campo `nome`; si usano le linee il cui nome inizia con `BC_`, con il centroide; in particolare `BC_caldonazzo` e `BC_brenta_valle` devono esistere.

## Output

* `WD/work/net.pkl`: dict `paths` (nome -> lista di id di nodi dello scheletro; chiave `main` per il tratto principale, una chiave per ogni altra `BC_*`) e `T` (nome -> nodo terminale).
* `WD/work/w.png`: figura 2 pannelli, larghezza del corridoio (bed+sponda) e del bed lungo il tratto principale (sopra, linea tratteggiata a 40 m) e larghezza corridoio degli affluenti (sotto, limite y 0-120 m).
* stdout: bounding box delle componenti 2-4, distanza (m) di ogni nodo terminale dal centroide della boundary, lunghezze dei cammini e punto di giunzione, percentili (0,5,50,95,100) delle larghezze, frazione del main con corridoio < 40 m e < 30 m, larghezze degli affluenti.

## Parametri e costanti

* Pesi: lunghezza dello spigolo (`weight`). `dist` (riga 19) è definita ma mai usata: la penalità per i bordi (commento originale) non è implementata.
* `smooth`: passo 1 m, sigma 8 campioni (8 m).
* `widths`: ogni 5 campioni, raggio di taglio ±600 m, salta 10 campioni a inizio/fine.
* Affluenti con meno di 40 campioni lisciati: saltati.

## Uso

```bash
python3 net.py /percorso/WD
```

## Funzionamento

1. Carica lo scheletro, prende la componente connessa maggiore `H`.
2. Per ogni boundary `BC_*` trova il nodo più vicino al centroide (`T`).
3. `main` = cammino minimo `BC_caldonazzo` -> `BC_brenta_valle`.
4. Per ogni altro terminale (dal più lontano dallo sbocco) Dijkstra su `H`, si prende il percorso fino al primo nodo già "fatto" (cioè del main); gli affluenti non vengono fusi tra loro.
5. Salva `net.pkl`.
6. Liscia i cammini e calcola per ogni punto la larghezza intersecando una retta perpendicolare lunga 1200 m con `cor` e con `bed`.
7. Stampa statistiche e salva il grafico.

## Verifiche e limiti

* "terminal dist" molto grande (> qualche decina di m) indica un terminale agganciato male.
* `done` si aggiorna solo con il main: tutti gli affluenti si ricongiungono al main (o ai suoi nodi), non tra loro.
* Larghezze NaN dove la normale non incrocia il poligono.
