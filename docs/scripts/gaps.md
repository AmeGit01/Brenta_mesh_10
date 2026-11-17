# gaps.py

Step 9. Controllo di connettività **solo a stampa**: individua gli estremi di linea che nel dato originale toccavano un'altra breakline (entro 1 mm) ma che, dopo l'allargamento, non toccano più nulla. Segue `apply_widen.py`, precede `place.py`. Non scrive file.

## Requisiti

* Python di Anaconda: shapely, numpy.
* Importa `core.py` (`pickle`, `shapely`, `LineString`, `Point`, `SP`).

## Input

* `WD/work/chains.pkl` (`chains.py`): `feat` (fid -> vertici originali).
* `WD/work/widen2.pkl` (`apply_widen.py`): `newf` (fid -> nuovi vertici delle feature cambiate); `endmap` viene letto ma non usato.

## Output

Solo stdout: prima il numero di estremi "rotti", poi fino a 60 tuple `(fid, estremo, xy nuovo, fid vicini originali (max 4), xy originale)`, dove estremo è `0` (primo vertice) o `-1` (ultimo). Atteso: `0`. Se > 0 gli estremi elencati vanno ispezionati o corretti.

## Parametri e costanti

* Tolleranza di contatto `1e-3` m (riga 10).
* Elenco limitato a 60 righe (riga 18).

## Uso

```bash
python3 gaps.py /percorso/WD
```

## Funzionamento

1. Costruisce due insiemi di `LineString`: originali (`old`) e allargati (`new`, con `newf` al posto degli originali) con relativi `STRtree`.
2. Per ogni feature e per ognuno dei due estremi cerca le altre linee entro 1 mm nel set originale e nel nuovo.
3. Se c'era almeno un vicino nell'originale e nessuno nel nuovo, registra l'estremo.

## Verifiche e limiti

* Le linee di `boundary.gpkg` (nodestring) non sono considerate, né nell'originale né nel nuovo.
* Considera solo i contatti agli estremi (un estremo che prima toccava e ora tocca una linea diversa passa il controllo).
* Il controllo vale contatti "estremo-su-linea" entro 1 mm, non verifica la planarità né l'assenza di sovrapposizioni.
