# bank.py

Calcola sul DTM i bankpoint (punto di sponda) sinistro e destro di ogni sezione a 50 m. È il passo 14 (precedente `next_bed.py`, successivo `finals.py`). Regola: lungo la sezione, dal piede verso l'esterno, si prende il primo massimo locale del profilo DTM con prominenza ≥ 5 cm, ignorando la metà inferiore dell'altezza della sponda; il punto deve stare ≥ 5 m all'interno del ciglio e a ≤ 15 m dalla mezzeria del canale (regola `mid`) oppure a ≤ 15 m dal piede (regola `toe15`). Se non c'è massimo valido si usa la cella più alta (fallback).

## Requisiti

* Interprete: **`/usr/bin/python3`** (di sistema), perché serve `osgeo`/GDAL; il Python di Anaconda non ha `osgeo`.
* Pacchetti: `osgeo.gdal`, numpy; stdlib `json`, `sys`, `math`, `collections`.
* Non importa `core.py` (autonomo), ma legge un file prodotto dagli script che lo usano.

## Input

* `WD/work/sec_in.json` (`export_sec.py`, poi `next_bed.py`): per ogni sezione usa `x`, `y`, `nx`, `ny`, `tL`, `tR`, `cL`, `cR` e, se presenti, `maxL`, `maxR`.
* `/home/amedeo/Documents/Brenta_mesh_10/layers/DTM_finale.tif` (percorso assoluto fisso nel codice): banda 1, celle 0.25 m, nodata −9999 (letto da `GetNoDataValue`).

## Output

* `WD/work/bank_out.json`: lista (stesso ordine di `sec_in.json`) di `{"L": {...}, "R": {...}}`. Campi di ciascun lato:
  * `kind`: `max` (massimo locale con prominenza), `fallback` (cella più alta), `muro`, `nobank`, `nodata`.
  * `t` (m): distanza dal centerpoint lungo la normale verso quel lato; è la posizione del bankpoint.
  * `z` (m, quota DTM; `null` per `nobank`/`nodata`), `prom` (prominenza in m, `null` se non applicabile), `rule` (`mid`, `toe15`, `muro`, `nobank`, `nocell`), `limit` (m, distanza limite di ricerca).
  * Solo per `max`, `fallback`, `muro`: `ztoe` (quota al piede), `zrange` (quota massima nella finestra; per `muro` è uguale a `z`).
* Stampa due Counter (uno per lato `L`, `R`) di coppie `(kind, rule)`. Consumato da `finals.py`, `regions.py`, `dump.py`, `check_bp.py`, `esplorativi/bq.py`.

## Parametri e costanti

* `DTM`: percorso del DTM, nella riga con `DTM=`, all'inizio dello script; modificare lì.
* `5.0` m: il bankpoint deve stare ≥ 5 m all'interno del ciglio (`cap5 = cc - 5`).
* `15.0` m: ampiezza della finestra oltre la mezzeria (`mid + 15`) o oltre il piede (`tt + 15`).
* `30` m: se la larghezza del letto `tL + tR` supera 30 m si usa direttamente la regola `toe15`.
* `2.0` m: se la finestra `mid` termina a meno di 2 m oltre il piede si passa a `toe15`.
* `0.05` m: prominenza minima (5 cm).
* `0.5`: frazione dell'altezza della sponda sotto cui i massimi sono ignorati (`thr = ztoe + 0.5*(zmax - ztoe)`).
* `60.0` m / `1500.0` m: il profilo si legge fino a `min(cc + 60, 1500)` dal centerpoint.
* `1e-9`, `1e-12`: tolleranze numeriche.

## Uso

```bash
/usr/bin/python3 bank.py /percorso/WD
```

## Funzionamento

1. Apre il DTM e legge origine (`X0`, `Y0`), dimensione cella (`PW`, `PH` positiva).
2. `traverse`: attraversamento esatto della griglia (algoritmo DDA) lungo il segmento `o + t·d`, `t ∈ [0, T]`; restituisce per ogni cella attraversata `(col, row, t_ingresso, t_uscita)`.
3. `read`: legge le quote delle celle con una sola `ReadAsArray` sul rettangolo che le contiene.
4. `analyse`: raggruppa celle consecutive di uguale quota in plateau, poi per ogni plateau interno più alto dei due vicini calcola la prominenza (valle più bassa verso sinistra/destra fino a un plateau più alto; prominenza = quota − max dei due colli; se nessun lato ha un plateau più alto, quota − minimo).
5. `side(sec, sgn, tt, cc, ...)` per un lato (`sgn=+1` sinistra, `−1` destra): calcola il limite `lim`:
   * `cap5 = min(cc − 5, maxL/maxR)`;
   * regola `mid`: `lim = min(cap5, mid + 15)`, con `mid = (cL − cR)/2` proiettato sul verso del lato; regola `toe15`: `lim = min(cap5, tt + 15)` se il letto è > 30 m o la finestra `mid` è < 2 m oltre il piede.
   * Se `lim ≤ tt` e il limite `max` ≤ piede: `muro` (punto al limite, quota dell'ultima cella).
   * Se `lim ≤ tt`: `nobank` (punto a metà tra piede e ciglio, senza quota).
   * Legge il profilo fino a `cc + 60`; se nessuna cella cade in `(tt, lim)`: `nobank/nocell`; se c'è una cella nodata nella finestra: `nodata`.
   * Soglia di quota `thr` (metà superiore); tra i massimi locali (che toccano `(tt, lim)`, con prominenza ≥ 0.05 e quota ≥ `thr`) sceglie il primo (distanza minore); `t` = metà del plateau limitata a `[tt, lim]`.
   * Altrimenti `fallback`: la cella più alta nella finestra.
6. Il ciclo principale applica `side` a sinistra e a destra per ogni sezione e scrive `bank_out.json`, poi stampa il riepilogo.

## Verifiche e limiti

* Verificare dai Counter stampati che prevalgano `max` con regole `mid`/`toe15` e che `nodata`, `nobank`, `muro` siano rari e giustificati (zone urbane per `muro`).
* `check_bp.py` ricalcola indipendentemente i bankpoint (campionamento a 1 cm) e li confronta con questo risultato.
* Il codice richiede che `sec_in.json` esista già e che `maxL`/`maxR` provengano da `next_bed.py`: eseguirlo prima di questo script.
* Il DTM è letto da percorso assoluto; se il progetto viene spostato va modificato.
* Le celle nodata sulla linea sono gestite solo come caso `nodata` (nessuna quota).
