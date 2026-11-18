# regions2.py

Secondo passo (2026-11-17). Sceglie **un punto regione per ogni faccia** del grafo planare finale (breakline corrette + nodestring + sezioni). I punti originali (fid ≤ 176) non vengono mai sostituiti; la coppia preesistente 57/58 resta; le facce senza un punto adatto ricevono un nuovo punto nel polo di inaccessibilità con gli attributi della regione originale da cui derivano. Precedente: `check_geom.py`; successivo: `prep_write.py`.

## Requisiti

* Interprete: `python3` di Anaconda (geopandas, shapely 2.1 con `polygonize`, `unary_union`, `polylabel`, numpy).
* Cartella di lavoro corrente = `WD`.

## Input

* `fix5.json` (chiave `F`, linee con ≥ 2 vertici), `secs_new.json`.
* `in/boundary_50m.gpkg` (nodestring non-sezione), `in/regioni_ponti_50m.gpkg` (punti attuali), `in0/regioni_ponti.gpkg` (punti originali).
* `work/newfaces.pkl` (`place.py`): `fc`, le facce di base per ritrovare la regione originale di una faccia.

## Output

* `WD/regions2.json`: `keep` (fid mantenuti), `drop` (fid da cancellare, ordinati), `new` (nuovi punti: `face`, `x`, `y`, `nome`, `mat_id`, `max_area`, `buco`, `clear`), `nfaces`.
* Stampa: numero di facce, facce con area < 1 m² e le aree minori; conteggi `kept`/`dropped`/`new`/`errors`; elenco dei punti eliminati, nuovi con distanza < 1 m, mantenuti con distanza < 1 m, nuovi per nome; stato dei punti 485, 504, 568.

## Parametri e costanti

* `1.0` m: distanza minima di un punto dalle linee (`clear >= 1.0`).
* `176`: i punti con fid ≤ 176 sono gli originali e hanno priorità (`key=(q>176,q)`).
* `{57, 58}`: coppia preesistente nella stessa faccia, lasciata com'è.
* `tolerance=0.02` m di `polylabel`; `1e-6`: tolleranza sul confronto delle distanze.
* Punti 485, 504, 568: solo stampati.

## Uso

```bash
cp scripts/regions2.py /percorso/WD/
```

```bash
cd /percorso/WD
```

```bash
python3 regions2.py
```

(layout di `WD`: vedi [dpB.md](dpB.md), sezione Uso.)

## Funzionamento

1. `U` = unione di breakline, nodestring e sezioni; `fc = polygonize(U)`.
2. `b0`: per ogni faccia di base di `newfaces.pkl`, i fid dei punti originali al suo interno. `infc`: punti attuali dentro ogni nuova faccia; `clear`: distanza di ogni punto da `U`.
3. Per ogni faccia `ps` = punti dentro, originali per primi:
   * contiene 57 e 58: li mantiene, elimina gli altri;
   * esiste un punto con `clear ≥ 1`: tiene il primo, elimina gli altri;
   * faccia stretta con punto originale: tiene quello con `clear` massima, mai sostituendo un originale;
   * altrimenti calcola `polylabel`; se un punto esistente ha `clear ≥` quella del polo lo tiene; se no crea un nuovo punto con gli attributi dell'originale della faccia di base (o del primo punto interno), eliminando i precedenti; se non si trova alcuna sorgente registra un errore.
4. Salva `regions2.json`.

## Verifiche e limiti

* Atteso: `errors []`. I nuovi punti con `clear < 1` e i mantenuti con `clear < 1` (facce strette) vanno esaminati.
* I fid dei nuovi punti sono assegnati solo in `prep_write.py`.
* Se una faccia contiene solo punti nuovi e non c'è un originale nella faccia di base, gli attributi vengono dal primo punto interno.
* Il numero di facce con area < 1 m² è solo informativo.
