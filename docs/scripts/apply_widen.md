# apply_widen.py

Step 8. Applica a tutto il set di breakline lo spostamento calcolato da `widen.py`: propaga gli estremi spostati alle linee che li toccano, fa scivolare gli estremi su linee non spostate, sposta gli estremi delle boundary, poi valida il nuovo grafo planare (linee semplici, facce, un punto regione per faccia). Segue `widen.py`, precede `gaps.py` e `place.py`.

## Requisiti

* Python di Anaconda: numpy, scipy, shapely 2.1, geopandas.
* Importa `core.py` (`pickle`, `gpd`, `np`, `shapely`, `LineString`, `Point`, `SP`, ...).

## Input

* `WD/work/chains.pkl` (`chains.py`): `feat`.
* `WD/work/widen.pkl` (`widen.py`): `newf`, `endT`, `bmove`, `bgeo`, `PTS`, `SH`, `DN` (gli ultimi tre sono caricati ma non usati).
* `WD/in/boundary.gpkg` (campo `nome` per i messaggi) e `WD/in/regioni_ponti.gpkg` (punti regione).

## Output

* `WD/work/widen2.pkl`: dict `newf` (`fid -> nuovi vertici` di **tutte** le breakline modificate: cigli spostati + linee dipendenti) e `endmap` (`(x,y) vecchio estremo arrotondato al mm -> nuovo xy`). Letto da `gaps.py`, `place.py`, `finals.py`, `regions.py`, `dump.py`.
* `WD/work/bgn.pkl`: dict `fid boundary -> nuovi vertici` solo per le boundary il cui estremo è stato spostato/estesa. Letto da `place.py`, `finals.py`, `regions.py`, `dump.py`.
* `WD/work/widen_faces.pkl`: dict `fc` (facce del grafo validato) e `A` (aree, m²). Non letto da altri script.
* stdout: numero di estremi spostati ("moved ends", "ends really moved"), feature dipendenti spostate, estremi fatti scivolare, boundary estese (nome, estremo, spostamento m), numero di linee non semplici nuove e originali, numero di facce e di facce < 1 m², facce per numero di punti, punti dentro una faccia, facce senza punto (area, centroide; max 20), facce con >= 2 punti.

## Parametri e costanti

* Chiave degli estremi: coordinate arrotondate a 3 decimali (1 mm).
* "Spostato" se > 1e-3 m; tolleranze di contatto `1e-3` m e `1e-6` m.
* Nessun parametro di larghezza: derivano da `widen.py`.

## Uso

```bash
python3 apply_widen.py /percorso/WD
```

## Funzionamento

1. `endmap`: per ogni feature in `newf`, vecchio -> nuovo estremo; aggiunge `endT`.
2. Le feature non spostate che hanno un estremo coincidente con un estremo spostato vengono modificate (stesso estremo spostato) e inserite in `newf`.
3. Per ogni feature spostata, se un estremo mosso era appoggiato a una linea **non** spostata, il nuovo estremo viene proiettato su quella linea originale (la connessione si mantiene).
4. Salva `widen2.pkl`.
5. Boundary: per i tag `('bd', k, e)` di `bmove` l'estremo `e` della boundary `k` viene portato sul nuovo ciglio; salva `bgn.pkl`.
6. Validazione: unione di tutte le linee nuove + boundary, `polygonize`, controllo linee non semplici, conteggio punti regione per faccia.

## Verifiche e limiti

* Atteso: nessuna linea non semplice nuova (confrontare con "non-simple orig"), nessuna faccia senza punto di area significativa, nessuna faccia con 2+ punti.
* Le feature dipendenti spostate in questo passo non vengono a loro volta usate per propagare ulteriormente.
* Il controllo di connettività agli estremi è demandato a `gaps.py`.
