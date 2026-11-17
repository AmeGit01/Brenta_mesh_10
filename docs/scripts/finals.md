# finals.py

Costruisce le sezioni finali come segmenti rettilinei a 2 vertici dal bankpoint sinistro (sx) al destro (dx), perpendicolari alla centerline, ed esegue controlli geometrici (solo stampa) contro breakline allargate, boundary e altre sezioni. È il passo 15 (precedente `bank.py`, successivo `regions.py`).

## Requisiti

* Interprete: `python3` di Anaconda.
* Pacchetti: numpy, shapely 2.x, geopandas (via `core.py`), `json`, `collections`.
* Modulo importato: `core.py` (`cls`, `boundary_segs`, `key`, `SP`, ecc.).

## Input

* `WD/work/sec_in.json` (`export_sec`/`next_bed`): `x`, `y`, `nx`, `ny`, `tL`, `tR`, `s`, `stream`.
* `WD/work/bank_out.json` (`bank.py`): `L.t`, `R.t`.
* `WD/work/widen2.pkl` (`apply_widen.py`): chiave `newf` = breakline spostate `{fid: array Nx2}`.
* `WD/work/chains.pkl` (`chains.py`): chiave `feat` = coordinate originali delle breakline `{fid: array}`.
* `WD/work/bgn.pkl` (`apply_widen.py`): coordinate dei boundary modificati `{fid: array}`.
* `WD/work/newfaces.pkl` (`place.py`): `fc`, `rows`.
* `WD/in/boundary.gpkg`: boundary originale (colonne `nome`, geometria).

## Output

* `WD/work/secs0.pkl`: lista di `LineString` a 2 vertici, nello stesso ordine di `sec_in.json`. Primo vertice `centerpoint + n·t_sinistro`, secondo `centerpoint − n·t_destro`. Consumato da `regions.py` e `dump.py`.
* Stampa (nessun altro file):
  * `crossing inner N bd N top N`: numero di sezioni (coppie) che intersecano rispettivamente linee interne, nodestring di boundary, linee di ciglio.
  * `bd list`, `inner` (Counter per fid di breakline), `detail`, `inner sec ids`, `top`: dettagli (iniziale stream, ascissa arrotondata, nome/fid, punto).
  * `section-section crossings N [...]`: coppie di sezioni che si incrociano.
  * `section length min median max` (m).

## Parametri e costanti

* `1e-4` m: tolleranza con cui un'intersezione singola è considerata coincidente col piede (e quindi ignorata).
* `[:40]`, `[:50]`: limiti di elenco nelle stampe.
* Classi usate: bed = `cls(nome)=='bed'`; ciglio = `cls` in `bed`, `sponda`, `muro`.

## Uso

```bash
python3 finals.py /percorso/WD
```

## Funzionamento

1. Carica input; per ogni boundary prende le coordinate modificate (`bgn`) o quelle originali.
2. Crea le 2 estremità di ogni sezione dai `t` dei bankpoint e salva `secs0.pkl`.
3. Contorni dalle facce di `newfaces.pkl`: `tb` (bordo del letto, piede), `tc` (bordo di bed+sponda+muro).
4. `inner`: segmenti di breakline (versione spostata se esiste) che non sono sul contorno `tb` né su `tc`, cioè linee interne.
5. Per ogni sezione: intersezioni con `inner` (ignorando il singolo punto che coincide col piede), con i boundary e con i segmenti `tc`.
6. Conta gli incroci sezione-sezione e le lunghezze delle sezioni.

## Verifiche e limiti

* Attesi: nessun incrocio sezione-sezione; incroci con linee interne e boundary da spiegare caso per caso (le liste stampate servono a questo).
* La lista `top` sembra elencare quasi tutte le sezioni, perché `tc` contiene anche il bordo del letto, che ogni sezione attraversa al piede; non è un test di fallimento.
* Nessuna asserzione: i controlli vanno letti a mano. Lo script scrive solo `secs0.pkl` (sovrascritto).
