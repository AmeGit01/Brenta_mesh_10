# skel.py

Step 2. Costruisce uno scheletro (asse mediano) del letto ("bed") tramite diagramma di Voronoi dei punti campionati lungo il contorno, e lo salva come grafo networkx. Segue `graph.py` e precede `net.py`. Lo scheletro più fine usato davvero per le centerline viene ricalcolato da `cl.py`; questo step è la prima versione, usata da `net.py`.

## Requisiti

* Python di Anaconda: geopandas, shapely, numpy, scipy (`Voronoi`), networkx.
* Non importa `core.py` (replica la logica di `cls` con le lambda `isbed`/`isbank`).

## Input

* `WD/work/graph.pkl` (`graph.py`): `faces`, `rows` (campi `face`, `nome`).

## Output

* `WD/work/skel.pkl`: dict `bed` (geometria dell'unione delle facce bed), `cor` (unione bed + sponda/muro, il "corridoio"), `g` (`networkx.Graph`, nodi = indici dei vertici di Voronoi, attributo `weight` = lunghezza dello spigolo in m), `vv` (array delle coordinate dei vertici di Voronoi). Letto da `net.py`.
* stdout: tipo di geometria, numero di parti e ettari di `bed` e `cor`; le 8 parti maggiori del bed (area, bounds, numero di buchi); numero di semi; dimensioni delle 6 componenti connesse maggiori dello scheletro.

## Parametri e costanti

* `buffer(0.02)` (righe 11-12): 2 cm per unire le facce adiacenti.
* Spaziatura semi `1.5` m (riga 20).
* Lunghezza massima spigolo `d<30` m (riga 29).
* `isbed`/`isbank` (righe 9-10): elenchi dei nomi di classe bed e sponda/muro; da tenere allineati con `core.cls`.

## Uso

```bash
python3 skel.py /percorso/WD
```

## Funzionamento

1. Carica `graph.pkl`; costruisce `bed` e `cor` come unione delle facce con buffer di 2 cm.
2. `P` = la parte unica del bed, oppure il multipoligono intero.
3. Campiona i contorni (esterno e buchi) ogni ~1.5 m.
4. `Voronoi` dei semi; tiene i vertici dentro `P`.
5. Crea il grafo con gli spigoli di Voronoi tra vertici interni, lunghi meno di 30 m e interamente contenuti in `P`.
6. Stampa le componenti connesse e salva.

## Verifiche e limiti

* Lo scheletro include rami laterali (baffi) verso rientranze del contorno; sono gestiti a valle (`net.py` usa i cammini minimi).
* La componente più grande dovrebbe attraversare tutto il fiume; verificare che le altre siano piccole.
* Con semi ogni 1.5 m la posizione dell'asse ha incertezza di circa questo ordine nei tratti stretti: per questo `cl.py` rifà lo scheletro con semi ogni 0.6 m.
