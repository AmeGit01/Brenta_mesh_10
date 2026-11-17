# cl.py

Step 4. Calcola le centerline grezze del canale principale ("asta", da `BC_caldonazzo` a `BC_brenta_valle`) e del Brenta vecchio come cammini di costo minimo su uno scheletro di Voronoi fine del letto; il costo favorisce il centro del canale. Segue `net.py`/`graph.py`, precede `cl2.py`.

## Requisiti

* Python di Anaconda: geopandas, shapely 2.1, numpy, scipy (`Voronoi`, `cKDTree`), networkx.
* Importa `core.py` (da `WD/work`): `load_graph`, `cls`, `Polygon`, `np`, `shapely`, `gpd`, `pickle`, `SP`.

## Input

* `WD/work/graph.pkl` (`graph.py`), tramite `load_graph()`: facce con classe `bed`.
* `WD/in/boundary.gpkg`, indicizzato per `nome`; usa i centroidi di `BC_caldonazzo`, `BC_brenta_valle`, `divergenza_valle_brenta_vecchio`, `boale_brenta_vecchio_monte`, `boale_brenta_vecchio_valle`, `check_portata_Brenta_vecchio`.

## Output

* `WD/work/rawcl.pkl`: dict `P` (poligono del letto usato per lo scheletro), `main` (array Nx2 dei vertici del cammino principale), `vecchio` (array Mx2 del Brenta vecchio). Coordinate EPSG:25832, non ancora lisciate né ricampionate. Letto da `cl2.py`.
* `WD/work/altmain.pkl`: array Nx2 di un percorso alternativo del tratto principale che passa dal meandro meridionale; solo confronto (letto da `esplorativi/up.py`).
* stdout: aree e centroidi dei buchi (isole), numero di semi, componenti connesse prima e dopo i collegamenti, contatti usati, lunghezza di main/vecchio, distanze di aggancio dei waypoint, distanze di testa/coda del vecchio dal main.

## Parametri e costanti

* `buffer(0.02)` m: unione delle facce bed.
* Isole: tenuti solo i buchi di area > 1000 m² (riga 10).
* Semi di Voronoi ogni **0.6 m** su tutti gli anelli (riga 12; il commento originale cita 0.5/1.5 m ma il codice usa 0.6 ovunque).
* Spigoli ammessi: lunghezza < 40 m; costo `c = d / max(min(distanza dal bordo dei due vertici), 0.15)` (riga 19), peso `w = d`.
* Componenti secondarie da collegare: >= 80 nodi; contatto ammesso se distanza <= 25 m; due contatti distinti a > 50 m tra loro; costo del ponte `2*distanza`.
* Punto "meandro" `(678150, 5096930)` (riga 46), waypoint manuali del Brenta vecchio `(687960, 5102512)` e `(688400, 5102655)` (riga 54), punto di confluenza `(689850, 5102944)` (riga 63): coordinate scelte a mano, da cambiare se cambia la geometria.

## Uso

```bash
python3 cl.py /percorso/WD
```

## Funzionamento

1. Unisce le facce `bed`; `P` = poligono esterno con le sole isole > 1000 m².
2. Voronoi dei punti campionati ogni 0.6 m sul contorno; tiene i vertici interni a `P` e gli spigoli < 40 m con costo che penalizza la vicinanza al bordo (distanza dal seme più vicino, minimo 0.15 m).
3. Le componenti connesse secondarie (>= 80 nodi) vengono collegate alle altre con al più due ponti tra i punti più vicini.
4. `A` e `Z` = nodi più vicini ai centroidi di `BC_caldonazzo` e `BC_brenta_valle`; `mp` = cammino a costo minimo `c`.
5. Percorso alternativo `A -> M1 -> Z` via meandro, salvato in `altmain.pkl` (in `try`; se fallisce stampa `alt fail`).
6. Brenta vecchio: concatena i cammini minimi (peso `w` = lunghezza) tra i waypoint ordinati, poi prolunga fino al punto di confluenza (689850, 5102944).
7. Stampa le lunghezze e salva `rawcl.pkl`.

## Verifiche e limiti

* Controllare "comps after": deve esserci una componente dominante; "bridged comp" mostra i contatti usati (distanze piccole = buon aggancio).
* "wp dist" elevato = waypoint agganciato a un nodo lontano.
* La variabile `order` (riga 26) è calcolata ma mai usata; `kdm` serve solo alle stampe finali.
* Il percorso a costo `c` segue il centro del canale: nelle zone molto larghe può "tagliare" tra isole; il lisciamento è in `cl2.py`.
* I waypoint hard-coded rendono lo script specifico a questo dataset.
