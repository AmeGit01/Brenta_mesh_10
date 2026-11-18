# dx_dev.py

Quarto passo (2026-11-18). Analisi statistica, in sola lettura, del passo dx tra sezioni consecutive dello stesso ramo, su due livelli:

* **Analisi 1, locale:** dx_dev per ogni coppia, cioè quanto una sezione è inclinata rispetto alla successiva;
* **Analisi 2, globale:** dx_dev_abs per un ramo o per l'intero modello, cioè quanto il passo più corto è inferiore al passo medio. È la grandezza che conta per il dt di un modello 1D esplicito (condizione CFL).

## Requisiti

* Interprete: `python3` di Anaconda (geopandas, shapely 2.1, numpy).

## Input

* Argomento 1: la cartella dei layer (`boundary_50m.gpkg`, `centerpoints_50m.gpkg`).
* Argomento 2: il CSV di uscita, normalmente `docs/Brenta_dx_dev_50m.csv`.

## Grandezze per coppia

Per la coppia i, formata dalle sezioni k e k+1 dello stesso ramo:

* **dx_avg,i:** distanza media tra le due sezioni. Ognuna si campiona in `NS` = 201 punti equidistanti; per ogni punto si misura la distanza dall'altra sezione (il segmento, non la retta). La media è su tutti i 402 punti, quindi è simmetrica.
* **dx_min,i:** distanza minima tra i due segmenti.
* **dx_max,i:** massimo delle distanze campionate.
* **dx_c,i:** distanza lungo la linea d'asse, cioè la differenza di `s_m`.
* **angolo** tra le due sezioni (gradi) e **larghezza** media (m).

## Analisi 1

**dx_dev,i = (dx_avg,i − dx_min,i) / dx_avg,i**

Vale 0 per sezioni parallele. Lo script stampa:

* le statistiche per ramo e in totale: media, mediana, deviazione standard, 90°, 95° e 99° percentile, massimo, coppie sopra 0.01, 0.02, 0.05 e 0.10, angolo e larghezza medi;
* la correlazione di dx_dev con l'angolo, con la larghezza e con larghezza · tan(angolo) / dx_avg;
* le 15 coppie con dx_dev più alto.

## Analisi 2

Su un insieme di coppie (ramo N, V, B o tutte insieme):

**dx_dev_abs = (media dx_avg − min dx_avg) / media dx_avg** (≥ 0)

In uno schema esplicito il passo temporale ammesso dalla condizione CFL è dt ≤ CFL · dx / (|u| + c). A parità di velocità, quindi, 1 − dx_dev_abs = min/media è il rapporto tra il dt fissato dal passo più corto e quello che si avrebbe con il passo medio. Lo script stampa:

* per ogni insieme: media e deviazione standard di dx_avg, minimo con la coppia che lo dà, massimo, dx_dev_abs, min/media, e la stessa grandezza calcolata sulla serie dei dx_c e su quella dei dx_min;
* i percentili dello scarto di ogni coppia dalla media del suo insieme, e_i = (dx_avg,i − media) / media, con il numero di coppie sotto −0.02, −0.05 e −0.10;
* la sensibilità: dx_dev_abs dell'intero modello togliendo le k coppie più corte (k = 0, 1, 2, 3, 5, 10);
* le 15 coppie con dx_avg più corto, le 10 con dx_min più corto e le 10 con dx_avg più lungo.

## Eccezioni

Le eccezioni sono quelle decise dall'utente il 18 novembre:

* **regola dei 5 m:** N16000, B00000, B00100, B00150, B00200, B00300, B00400, B00450, B00500;
* **passo:** N01900–N01950, B11200–B11250, B00250–B00300–B00350.

Una coppia è esclusa dalle statistiche "senza eccezioni" se almeno una delle due sezioni è un'eccezione. Le coppie escluse sono 19. Ogni tabella è data con tutte le coppie e senza eccezioni.

## Output

* Il CSV, con una riga per coppia e le colonne `sez_monte`, `sez_valle`, `ramo`, `dx_c`, `dx_avg`, `dx_min`, `dx_max`, `dx_dev`, `ang_gradi`, `larg_m`, `e_avg_ramo` (scarto dalla media del ramo, calcolata su tutte le coppie) ed `eccezione` (1 se esclusa).
* Le tabelle Markdown delle due analisi, stampate a video.

## Uso

```bash
python3 scripts/dx_dev.py layers docs/Brenta_dx_dev_50m.csv
```

## Limiti

* dx_avg pesa allo stesso modo due sezioni di larghezza molto diversa.
* L'analisi è solo geometrica: non tiene conto di dove scorre davvero l'acqua, né delle velocità, che nella CFL contano quanto il passo.
