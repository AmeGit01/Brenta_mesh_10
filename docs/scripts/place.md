# place.py

Step 10. Genera candidati di posizione della sezione ogni 0.25 m lungo le due centerline e li valuta: distanze da piede e ciglio, regola dei 5 m dai vertici del piede, incroci con le boundary e con le breakline interne. Costruisce anche il nuovo grafo planare (breakline allargate + boundary nuove) con le facce e i loro nomi. La scelta delle stazioni a 50 m è fatta da `dp.py`. Segue `gaps.py`/`apply_widen.py`.

## Requisiti

* Python di Anaconda: numpy, scipy (`cKDTree`), shapely 2.1, geopandas.
* Importa `core.py`: `cls`, `key`, `boundary_segs`, `Rays`, `gpd`, `pickle`, `shapely`, `LineString`.

## Input

* `WD/work/cltab.pkl` (`cl2.py`): `q` di `main` e `vecchio`.
* `WD/work/widen2.pkl` (`apply_widen.py`): `newf`.
* `WD/work/chains.pkl` (`chains.py`): `feat`.
* `WD/work/bgn.pkl` (`apply_widen.py`): boundary modificate.
* `WD/in/boundary.gpkg`, `WD/in/regioni_ponti.gpkg` (campo `nome`).

## Output

* `WD/work/newfaces.pkl`: dict `fc` (facce del grafo planare nuovo) e `rows` (lista di `{face, nome}`, una per faccia con almeno un punto regione; vale il primo punto). Letto da `finals.py`, `regions.py`, `next_bed.py`, `final.py`.
* `WD/work/cands.pkl`: dict `{'main': ..., 'vecchio': ...}`, ciascuno con array allineati per candidato:
  * `ss`: progressiva (m, passo 0.25); `P`: xy sulla centerline; `n`: normale sinistra unitaria;
  * `tL`, `tR`: distanza centerline-piede sul lato t>0 e t<0 (m); `cL`, `cR`: centerline-ciglio;
  * `pen5`: 0..2, numero di lati in cui l'incrocio con il piede cade a meno di 5 m da un vertice del piede;
  * `hitB`: 1 se la sezione approssimata interseca una boundary; `hitO`: 1 se interseca una breakline interna;
  * `ok`: True se piede e ciglio sono stati trovati su entrambi i lati.
  Letto da `dp.py` e `export_sec.py`.
* stdout: numero di facce e di facce con nome; numero di vertici del piede; numero di ostacoli (boundary, segmenti interni); per ciascuna centerline numero di candidati, validi, quanti toccano boundary / linee interne / violano la regola dei 5 m.

## Parametri e costanti

* `GR = 0.25` m (riga 43): passo dei candidati.
* Tangente per la normale: corda tra `s-1` e `s+1` m.
* Raggio dei raggi ±1500 m.
* Regola dei 5 m (riga 68): l'incrocio con il piede non deve cadere a meno di 5 m da un vertice del piede (se un vertice coincide, <= 1 mm, si usa il successivo).
* Estensione approssimata della sezione (righe 70-72): `min(t+15, c-5)` (15 m oltre il piede ma 5 m dentro il ciglio); se la larghezza è <= 30 m si limita a `max(t+0.5, c-5)`. Nota: per il lato sinistro il test è `tL+cR > 30`, per il destro `tL+tR > 30` (asimmetria come scritta).
* Tolleranza `1e-3` m, `1e-6`.

## Uso

```bash
python3 place.py /percorso/WD
```

## Funzionamento

1. Carica dati e costruisce il grafo planare nuovo (linee `newf` o originali + boundary `bgn` o originali); `polygonize`; assegna il nome ai punti regione per faccia; salva `newfaces.pkl`.
2. `tb` (piede) e `tc` (ciglio) dal nuovo grafo; oggetti `Rays`.
3. `vtx`: vertici delle breakline che contengono almeno un segmento di piede; `KD-tree` `vk`.
4. Ostacoli: `OT` = boundary; `OTB` = segmenti singoli di breakline che non sono né piede né ciglio (linee interne: cross-line, edifici).
5. Per `main` e `vecchio`: `cand()` crea i candidati, `eval_cand()` valuta distanze piede/ciglio; calcola `pen5`, l'estensione approssimata, `hitB`, `hitO`.
6. Salva `cands.pkl`.

## Verifiche e limiti

* Le variabili `toev` (riga 20, `None`) e `obs` (righe 28-32) sono codice morto.
* L'estensione della sezione è approssimata: le sezioni finali sono costruite dagli script successivi (`export_sec.py`, `finals.py`).
* Un candidato con `ok=False` o toccato da boundary è praticamente escluso da `dp.py` (penalità).
* Le facce senza punto regione non hanno nome e non entrano nei piedi/cigli.
