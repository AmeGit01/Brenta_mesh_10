# check_bp.py

Verifica indipendente dei bankpoint salvati in `layers/bankpoints_50m.gpkg`: ricalcola ogni bankpoint con un metodo diverso da `bank.py` (profilo campionato ogni 1 cm invece dell'attraversamento esatto delle celle) e confronta; controlla anche `z_dtm` contro il DTM e la regola dei 5 m dal ciglio. Gruppo 19 (controlli dopo `write.py`). Solo stampa.

## Requisiti

* Interprete: **`/usr/bin/python3`** (serve `osgeo`; il Python di Anaconda non ce l'ha). Pacchetti: `osgeo.gdal`, `osgeo.ogr`, numpy; stdlib `json`, `sys`, `math`.
* Importa anche `sqlite3` e `struct`, ma non li usa. Non importa `core.py`.

## Input

* `WD/work/sec_in.json` (incluso `maxL`/`maxR` di `next_bed.py`).
* `/home/amedeo/Documents/Brenta_mesh_10/layers/DTM_finale.tif`, `bankpoints_50m.gpkg` (campi `nome`, `z_dtm`, `tipo`, `regola`, `dist_cp`, geometria), `boundary_50m.gpkg` (layer `boundary`, nomi `S#####`/`V#####`, conteggio e stampa `sec layer N`).

## Output

Solo stampa:

* `sec layer N`: numero di sezioni lette.
* `12 z_dtm mismatch A of N ; bankpoints closer than 5 m to top B`.
* `13 independent 1-cm bankpoint comparison: differences N [...]`: elenco (max 20) di `(sezione, lato, tipo salvato, tipo ricalcolato, z salvata, z ricalcolata)`.
* Righe `residual ...` per i casi non spiegabili dal campionamento.
* `in-range stretch of winning cell (m) [...] ; at most 1 cm: K of N`.

## Parametri e costanti

* `0.01` m: passo del campionamento (`step`).
* `1e-6` m: tolleranza del controllo `z_dtm`; `1e-3` m: tolleranza sulla quota nel confronto 13.
* `5.0` m dal ciglio; `15.0` m; `30` m; `2.0` m; `0.05` m di prominenza; metà altezza per la soglia; `60.0` e `1500.0` m: stessi valori e significato di `bank.py`.
* `0.0105` m: soglia oltre la quale una differenza è stampata come `residual`.

## Uso

```bash
/usr/bin/python3 check_bp.py /percorso/WD
```

## Funzionamento

Controlli eseguiti e criterio di superamento (non asseriti dal codice):

1. **12a, `z_dtm`**: per ogni bankpoint legge la cella DTM che lo contiene e confronta con `z_dtm` (differenza > 1e-6 = errore). Criterio: 0.
2. **12b, 5 m dal ciglio**: conta i bankpoint (esclusi `muro`) con `dist_cp > cL/cR − 5 + 1e-6`. Criterio: 0.
3. **13, ricalcolo indipendente** per ogni bankpoint non `muro`: ricostruisce il limite `lim` (stessa regola `mid`/`toe15`, tetto `maxL/maxR`), campiona il profilo ogni 1 cm fino a `min(cc + 60, 1500)`, raggruppa in run di valore uguale, trova i massimi locali con prominenza ≥ 5 cm e quota ≥ soglia di metà altezza, prende il primo; altrimenti il campione più alto (`fallback`). Differenza se il tipo (`max`/`fallback`) o la quota (> 1 mm) non coincidono con quelli salvati.
4. **Spiegazione delle differenze**: per ogni differenza calcola la lunghezza (m) del tratto della cella scelta da `bank.py` che cade dentro la finestra valida; se ≤ 1 cm (0.0105) il campionamento a 1 cm non poteva vederla (artefatto di campionamento); se maggiore stampa `residual`. Criterio: nessuna riga `residual`, cioè `at most 1 cm: K of N` con K = N.

## Verifiche e limiti

* Per i bankpoint di tipo `nobank` o `nodata`, `z_dtm` è nullo e la differenza `abs(v - z)` darebbe errore; il controllo presuppone che questi casi non esistano. Inoltre il ricalcolo conosce solo `max`/`fallback`, quindi tali casi risulterebbero differenze.
* I bankpoint `muro` sono controllati solo per `z_dtm`.
* La lettura del DTM per cella usa `floor` sulle coordinate; punti esattamente su un bordo di cella possono essere ambigui.
