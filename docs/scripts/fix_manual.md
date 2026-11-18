# fix_manual.py

Quarto passo (2026-11-18). Ripara gli effetti collaterali delle sezioni modificate a mano in QGIS, senza spostare in pianta nessun vertice di sezione o di nodestring. Non scrive nei layer: prepara il file per `write3.py`.

## Requisiti

* Interprete: `python3` di Anaconda (geopandas, shapely 2.1, numpy).

## Input

* Argomento 1: la cartella dei layer, con i `*_50m.gpkg` correnti e gli originali `breaklines.gpkg`, `boundary.gpkg` e `regioni_ponti.gpkg`.
* Argomento 2: `mat11_lines.json` (`prep_inputs_nvb.py`), le 32 breakline dei muri, che sono bloccate.
* Argomento 3: il file JSON di uscita.

## Output

Il file JSON contiene `bd` (sezioni con la sola quota corretta), `bl` (breakline con il vertice spostato) e `reg_new` (nuovi punti regione). La stampa riporta ogni intervento.

## Cosa fa

1. **Quote delle sezioni.** Se un vertice di sezione ha z o m diversi da 0, li porta a 0 senza toccare x e y. Capita quando in QGIS si aggancia il vertice a una linea 3D. Il 18 novembre è successo alla B00300, agganciata a `edificio_borgo_sx_2`: aveva z = 381.76.
2. **Incroci quasi coincidenti con un vertice.** Se una sezione incrocia una breakline a meno di `NEAR` = 5 cm da un vertice, ma non esattamente sul vertice, il vertice viene spostato sull'incrocio. Lo spostamento vale per tutte le breakline che lo condividono, secondo la regola per cui si sposta la breakline e mai la nodestring. Se il vertice appartiene a una nodestring o a una linea dei muri bloccata, il caso viene solo segnalato.

   Il 18 novembre:
   * il nodo delle linee 894/895 si è spostato di 2.0 mm sull'incrocio con B00400 / `idrometro_Borgo`, che erano state allungate;
   * un vertice della 895 si è spostato di 1.2 mm sull'incrocio con la B00500, che era stata ruotata.
3. **Facce senza punto regione.** Ricostruisce il grafo planare con le breakline corrette e tutte le linee del boundary. A ogni faccia senza punto dà un punto nel polo di inaccessibilità (`polylabel`, tolleranza 1 cm). Gli attributi sono quelli della regione originale la cui faccia, nel grafo dei dati originali, contiene quel punto. Se l'origine è ambigua o manca, il caso viene solo segnalato.

   Il 18 novembre ha creato 5 punti `bed_borgo` (`mat_id` 13, `max_area` 5, attributi del fid originale 134). Sono le facce del letto tra B00100 e B00400, che si sono chiuse quando le sezioni sono state prolungate fino ai muri.

Infine segnala gli estremi di sezione che si trovano tra 0 e 1 cm da una linea senza toccarla. Il 18 novembre erano tutti a meno di 5 µm, che è il normale arrotondamento dello snap di QGIS.

## Uso

```bash
python3 scripts/fix_manual.py layers /percorso/WD/mat11_lines.json /percorso/WD/write3b.json
```

Poi:

```bash
/usr/bin/python3 scripts/write3.py /percorso/WD/write3b.json <tag>
```

## Verifiche e limiti

* Gli spostamenti sono pensati per correzioni millimetriche (`NEAR` = 5 cm). Non sostituiscono la regola dei 5 m: per quella c'è `fix5.py`.
* Un nuovo punto regione eredita gli attributi della regione originale nel punto in cui cade. Se l'allargamento delle sponde ha cambiato la natura di quella zona, l'attribuzione va controllata, come fa `verify3.py` al punto 25.
