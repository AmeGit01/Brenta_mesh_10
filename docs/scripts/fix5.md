# fix5.py

Secondo passo (2026-11-17). Applica la regola dei 5 m alle breakline: nessun vertice di breakline a distanza in `(1 mm, 5 m)` da un incrocio sezione/breakline (o nodestring/breakline). Gli incroci non si spostano: sono inseriti come vertici; si rimuovono o spostano i vertici vicini. Precedente: `assemble.py`; successivi: `check5.py`, `check_geom.py`, `regions2.py`.

## Requisiti

* Interprete: `python3` di Anaconda (geopandas, shapely 2.1, numpy, `collections`).
* Percorsi **relativi**: cartella di lavoro corrente = `WD`. Non importa `core.py`. (`pickle` è importato ma non usato.)

## Input

* `in/breaklines_50m.gpkg`, `in/boundary_50m.gpkg`, `in/regioni_ponti_50m.gpkg` (copie dei layer attuali).
* `secs_new.json` (`assemble.py`).
* `mat11_lines.json` (`prep_inputs_nvb.py`): breakline dei muri (`mat_id` 11), bloccate.

## Output

* `WD/fix5.json`: `F` (fid → lista di vertici di **tutte** le breakline), `log` (operazioni `del`/`move`/`slide`), `unres` (incroci non risolti), `XS` (incroci sezione/breakline come `(sezione, fid, punto)`).
* Stampa: vertici di T-giunzione aggiunti (all'inizio e dopo), corrispondenze dei casi speciali (1225, 988), numero di incroci, conteggi `removed`/`moved`/`slid`/`unresolved` con l'elenco dei non risolti, numero di feature cambiate e feature collassate.

## Parametri e costanti

* `TOL = 2.0` m: deviazione massima della rete di linee per una singola operazione.
* `5.0` m e `1e-3` m: finestra `(1 mm, 5 m)` della regola; `5.05` m: distanza minima target negli spostamenti per scorrimento (`slide`) e per 988; passo di scorrimento 0.01 m, massimo 6 m.
* `1 m`: i punti regione non devono avvicinarsi alle linee più di `min(distanza precedente, 1 m)`.
* `40`: massimo di iterazioni per incrocio. `1e-6`, `1e-7`, `1e-9`: tolleranze (chiave `R6` = coordinate arrotondate a 1e-6).
* Casi speciali scritti nel codice: breakline `1225` (sezione `N15050`, punto regione 485), `987` e `988` (sezione `N11750`, striscia `source_3_brenta_3`).
* Nodestring non-sezione: nomi diversi da `[SV]` + 5 cifre (il layer `in/` ha ancora le sezioni S/V).

## Uso

```bash
cp scripts/fix5.py /percorso/WD/
```

```bash
cd /percorso/WD
```

```bash
python3 fix5.py
```

(layout di `WD`: vedi [dpB.md](dpB.md), sezione Uso.)

## Funzionamento

1. `F` = vertici delle breakline; `SEC` = nuove sezioni; `NS` = nodestring non-sezione.
2. `add_tjunctions()`: ogni estremo di una linea che giace all'interno di un'altra diventa un vertice di quest'ultima, così rimuovere vertici non può staccare una linea e unire due regioni.
3. Punto 485: gli estremi della breakline 1225 (posata sulla sezione `N15050`) scorrono lungo i piedi su cui giacciono fino agli incroci con la sezione.
4. `N11750`: gli estremi di 987 sono spostati sugli incroci della sezione con le linee ospitanti; quelli di 988 scorrono a valle fino a ≥ 5.05 m dall'incrocio.
5. `insert_crossings`: inserisce come vertice ogni incrocio sezione/breakline (`XS`) e nodestring/breakline (`XN`); salta le breakline posate sulla linea (1225, 987).
6. `fixed` = incroci, vertici delle nodestring, vertici sulle nodestring e tutti i vertici delle linee bloccate (`LOCK`, da `mat11_lines.json`): non si muovono mai. Nelle linee bloccate non si inseriscono incroci né vertici di T-giunzione e non si tolgono nemmeno i vertici doppi. Restano identiche all'originale; gli incroci con le sezioni vengono comunque registrati in `XS`. `ok_change(old,new)` valida ogni operazione: deviazione ≤ `TOL`, punti regione non più vicini, linee semplici, nessun nuovo incrocio.
7. Ciclo su ogni incrocio `C`: finché c'è un vertice a distanza `(1 mm, 5 m)` (esclusi gli incroci della stessa sezione):
   * vertice interno di una sola linea: lo rimuove se valido;
   * giunzione o estremo: cerca (DFS) un percorso da `C` di vertici rimovibili entro 5 m; se esiste li rimuove e sposta la giunzione su `C` (una sola giunzione per incrocio);
   * vertice di nodestring: non risolvibile.
8. T-giunzioni sulle linee cambiate; `slide(k)`: per i non risolti (giunzioni/estremi non fissi) fa scorrere il punto lungo le due linee più collineari (la catena del piede) fino a ≥ 5.05 m da ogni incrocio, se valido.
9. Salva `fix5.json`.

## Verifiche e limiti

* Eseguire `check5.py fix5.json` (controllo indipendente) e `check_geom.py`; l'elenco `unresolved` deve essere vuoto o giustificato.
* Il codice contiene residui: `snap_all()` è vuota e la prima definizione di `chg` è sostituita dalla seconda.
* Se `in/boundary_50m.gpkg` contenesse già sezioni N/B, il filtro `[SV]` le tratterebbe come nodestring.
* La validazione usa distanze di Hausdorff discrete (punti ogni 0.25 m);.
* I numeri di fid e i nomi dei casi speciali (1225, 987, 988, N15050, N11750) sono fissi nel codice.
* Se una sezione coincide con una nodestring (dal 18 novembre B00400 = `idrometro_Borgo`), i suoi incroci coincidono con quelli della nodestring. Lo script li tratta come incroci di sezione e li inserisce una volta sola.
