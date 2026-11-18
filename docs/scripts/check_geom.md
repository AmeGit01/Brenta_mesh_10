# check_geom.py

Secondo passo (2026-11-17). Confronta le breakline corrette (`fix5.json`) con quelle attuali: gli incroci non devono spostarsi, la deviazione deve essere piccola, e non devono comparire nuovi incroci linea-linea. Precedente: `fix5.py`; successivo: `regions2.py`.

## Requisiti

* Interprete: `python3` di Anaconda (geopandas, shapely, numpy).
* Cartella di lavoro corrente = `WD`.

## Input

* `in/breaklines_50m.gpkg`, `in/boundary_50m.gpkg`, `fix5.json`, `secs_new.json`.

## Output

Solo stampa: (1) punti di incrocio prima dell'intervento non più sulla nuova rete (`lost`, atteso 0); (2) punti di incrocio dopo che non erano sulla vecchia rete (atteso 0); (3) numero di breakline cambiate, massimo/mediana della distanza di Hausdorff, quante oltre 0.5 e 1 m; (4) incroci linea-linea prima/dopo e quelli nuovi (atteso lista vuota).

## Parametri e costanti

* `special = {1225, 987, 988}`: breakline escluse dal confronto degli incroci (posate sulla sezione o scorse a mano).
* `1e-4` m: tolleranza di appartenenza di un punto alla rete; `1e-9`: soglia per dichiarare una linea cambiata.
* Le linee confrontate: sezioni nuove e nodestring non-sezione (nomi diversi da `[SV]` + 5 cifre).

## Uso

```bash
cp scripts/check_geom.py /percorso/WD/
```

```bash
cd /percorso/WD
```

```bash
python3 check_geom.py
```

(layout di `WD`: vedi [dpB.md](dpB.md), sezione Uso.)

## Funzionamento

`X(D)` produce il conteggio dei punti di incrocio (nome linea, x, y arrotondati) tra sezioni/nodestring e un insieme di breakline. Si calcola per l'insieme vecchio (`O`) e nuovo (`N`) e si verifica che ogni punto sia presente nell'altra rete (distanza ≤ 1e-4 m dall'unione). Poi calcola la distanza di Hausdorff per ogni breakline modificata e confronta le coppie di linee che si incrociano propriamente (`crosses`) prima e dopo.

## Verifiche e limiti

* Esito atteso: 0 incroci persi, 0 nuovi, nessun nuovo incrocio linea-linea; la deviazione massima deve restare entro `TOL = 2 m` di `fix5.py` (la distanza di Hausdorff può essere però maggiore di quella per operazione).
* Le sezioni di confronto sono le **nuove**: gli incroci delle vecchie sezioni non sono considerati.
* Le breakline `special` non sono verificate qui.
