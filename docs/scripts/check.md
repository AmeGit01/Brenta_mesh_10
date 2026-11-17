# check.py

Verifica generale dei file `layers/*_50m.gpkg` riletti dal disco, confrontati con gli originali. È nel gruppo 19 della sequenza (controlli dopo `write.py`; vedi `README.md`). Non scrive nulla e non fa asserzioni: stampa righe numerate 1-11 che vanno confrontate a mano con i criteri sotto.

## Requisiti

* Interprete: `python3` di Anaconda.
* Pacchetti: numpy, shapely 2.x, geopandas, `sqlite3`, `collections`.
* Non importa `core.py` e **non prende argomenti** (non usa `WD`).

## Input

In `/home/amedeo/Documents/Brenta_mesh_10/layers/` (percorso fisso): `breaklines`, `boundary`, `regioni_ponti` (originali) e `breaklines_50m`, `boundary_50m`, `regioni_ponti_50m`, `centerline_50m`, `centerpoints_50m`, `bankpoints_50m` (prodotti da `write.py`).

## Output

Solo stampa. Nessun file scritto.

## Parametri e costanti

* `L`: cartella `layers`.
* `49.5`–`50.5` m: intervallo ammesso tra sezioni consecutive (50 ± 0.5), tolleranza `1e-6`.
* `±1 m` sulla centerline per la tangente (`sc-1`, `sc+1`).
* `0` come tolleranza di `equals_exact` nel controllo 4 (identità bit a bit).

## Uso

```bash
python3 check.py
```

## Funzionamento

Controlli eseguiti (il codice non fa asserzioni; il "criterio" è quello atteso dal progetto):

1. **Conteggi**: numero di feature di breaklines, boundary (originale + nuove), regioni, centerline, centerpoints, bankpoints. Criterio: boundary = originale + numero di sezioni; centerpoints = numero di sezioni; bankpoints = 2 × sezioni; centerline = 2.
2. **Nomi/ID**: `bd.nome` e `bd.id` unici (`True`), primo e ultimo nome delle nuove sezioni, numero di nuove sezioni, intervalli di fid e id, numero di nomi con `S` e con `V`. Criterio: unicità vera; `S` + `V` = nuove sezioni.
3. **Integrità GPKG** per `breaklines`, `boundary`, `regioni_ponti` (`_50m`): `pragma integrity_check` (atteso `ok`), `feature_count` in `gpkg_ogr_contents`, righe nella tabella rtree, righe nella tabella, `srs_id` (atteso 25832), tipo geometria/Z/M. Criterio: conteggi coerenti (l'rtree può avere meno righe se esistono geometrie vuote nell'originale); stampa anche i campi delle tabelle.
4. **Feature invariate**: numero di breakline, boundary e regioni con geometria identica all'originale (tolleranza 0) rispetto al totale, e fid delle regioni eliminate. Criterio: solo le feature volutamente modificate/eliminate differiscono.
5. **Spaziatura** per ciascun stream: `ds` (differenza di `s_m`) e distanza rettilinea `ch` tra centerpoint consecutivi nell'intervallo [49.5, 50.5]; numero di valori fuori; max |`s_m` − proiezione del centerpoint sulla centerline|; primo `s`; distanza dell'ultima sezione dalla fine. Criterio: 0 fuori intervallo (sia `ds` sia `ch`), differenza `s` molto piccola.
6. **Perpendicolarità**: deviazione massima in gradi tra la sezione e la normale alla corda della centerline (`s ± 1 m`); numero di sezioni con primo vertice a sinistra nel verso di percorrenza. Criterio: deviazione ≈ 0 e conteggio = numero di sezioni dello stream.
   * Controllo associato: ogni sezione ha 2 vertici e i vertici coincidono con i bankpoint `_sx`/`_dx` (`np.allclose`); `errors … : 0` atteso.
7. **Incroci sezione-sezione**. Criterio: 0.
8. **Incroci sezioni vs altri nodestring** (boundary originali): numero e primi nomi. Criterio: 0 (se > 0, i nomi sono elencati).
9. **Grafo planare** (breakline + boundary, con sezioni): numero di facce, area minima, istogramma dei punti regione per faccia, fid di facce con > 1 punto, punti fuori da ogni faccia. Criterio: ogni faccia con esattamente 1 punto, nessun punto fuori.
10. **Breakline toccate da ogni sezione**: istogramma del numero di breakline intersecate (informativo).
11. **Bankpoint per `tipo` e `regola`**: conteggi (informativo; `max`/`mid`/`toe15` dovrebbero prevalere).

## Verifiche e limiti

* Il confronto con i criteri è manuale: lo script non termina con errore se un criterio fallisce.
* Il controllo 6 usa `np.cross` su vettori 2D: con numpy ≥ 2.0 può emettere un avviso di deprecazione.
* Il controllo 3 assume che nei file esistano le tabelle `gpkg_ogr_contents` e rtree create da GDAL.
