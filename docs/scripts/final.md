# final.py

Controlli finali sui layer scritti (regola dei 5 m, distanza dei nuovi punti regione dalle linee) ed esportazione della tabella CSV delle sezioni. Gruppo 19 (dopo `write.py`).

## Requisiti

* Interprete: `python3` di Anaconda.
* Pacchetti: numpy, shapely 2.x, geopandas, scipy (`cKDTree`), `csv`, `json`.
* Modulo importato: `core.py` (`boundary_segs`, `cls`, `key`, `pickle`, `SP`, ...).

## Input

* `layers/breaklines_50m`, `boundary_50m`, `regioni_ponti_50m`, `bankpoints_50m`, `centerpoints_50m` (`.gpkg`, percorso assoluto `/home/amedeo/Documents/Brenta_mesh_10/layers`).
* `WD/work/newfaces.pkl` (`fc`, `rows`): usato per costruire `tb`, `tk`, che poi non servono.

## Output

* `/home/amedeo/Documents/Brenta_mesh_10/docs/Brenta_sections_50m_mesh10.csv` (percorso assoluto; **sovrascritto**), una riga per sezione, colonne: `sezione s_m z_sx dist_cp_sx tipo_sx regola_sx prom_sx z_dx dist_cp_dx tipo_dx regola_dx prom_dx lunghezza_m` (`prom` vuoto se nullo; lunghezza = distanza sx-dx in m). Ordine = ordine dei centerpoint nel layer.
* Stampa:
  * `toe lines N`: numero di breakline considerate.
  * `5 m rule: crossings N with a vertex in (0,5) m V sections S min dist D`.
  * `5 m rule below 0.5 m: [...] count K`.
  * `regioni by nome {...}` (12 nomi più frequenti).
  * `new points clear D <1 m: [...]`.
  * `csv N`.

## Parametri e costanti

* `5.0` m: raggio della regola dei 5 m.
* `1e-3` m: distanze ≤ a questo valore sono considerate coincidenti col punto di incrocio e ignorate.
* `0.5` m: soglia della seconda stampa della regola dei 5 m.
* `176`: fid massimo dei punti regione originali (hard-coded; i nuovi punti sono quelli con fid > 176). Va cambiato se l'originale cambia.
* `1` m: soglia di distanza dei nuovi punti regione.
* Percorsi assoluti di `layers` e del CSV in testa/in fondo allo script.

## Uso

```bash
python3 final.py /percorso/WD
```

## Funzionamento

1. Legge i layer `_50m` e separa le sezioni (nomi `S`/`V` + 5 cifre) dagli altri boundary.
2. Dalle breakline `_50m` (tutte, nonostante la variabile si chiami `toe`) costruisce un KD-tree dei vertici e un indice spaziale.
3. **Regola dei 5 m**: per ogni sezione calcola i punti di incrocio con le breakline; per ognuno cerca i vertici di breakline entro 5 m (escludendo quello coincidente entro 1 mm); se ne esiste uno è una violazione. Stampa conteggi, numero di sezioni coinvolte, distanza minima e i casi sotto 0.5 m (primi 15).
4. Conta i punti regione per nome e calcola la distanza dei punti nuovi (fid > 176) da tutte le linee (breakline e boundary); elenca quelli a meno di 1 m.
5. Costruisce e scrive il CSV.

## Verifiche e limiti

* Criteri attesi (non asseriti): nessun punto nuovo a < 1 m dalle linee (o solo casi giustificati: `regions.py` indica "quando possibile"); le violazioni della regola dei 5 m sono da valutare, soprattutto quelle sotto 0.5 m. Il numero di righe del CSV deve essere il numero di sezioni.
* Se non ci sono violazioni, `min(v[2] for v in viol)` solleva `ValueError` (lista vuota): in quel caso lo script si ferma prima di scrivere il CSV.
* Il CSV viene sovrascritto senza backup.
