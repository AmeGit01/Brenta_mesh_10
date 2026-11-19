# fix_bridges.py

Quinto passo (2026-11-19). Elimina le strisce sottilissime tra le breakline di chiusura dei ponti e le nodestring dei ponti. Si sposta la breakline, mai la nodestring. Non scrive sui layer: prepara il payload per `write3.py`.

## Perché

In origine le breakline 1113, 1116, 1118 e 1421 erano copie esatte delle nodestring `P17_monte`, `P20_valle`, `P27_valle` e `P13_monte_idrometro_Ponte_Cervia`. Il 9 novembre sono state prolungate fino ai nuovi cigli. Poi nel tratto in comune hanno perso i vertici della nodestring e hanno preso vertici intermedi a 10⁻¹¹–10⁻¹⁰ m da essa. Le due linee non coincidevano più, e tra loro si formavano 5 facce larghe circa 10⁻⁸ m.

## Requisiti

* Interprete: `python3` di Anaconda (geopandas, shapely 2.1, numpy).

## Input

* Argomento 1: la cartella dei layer (`breaklines_50m`, `boundary_50m`, `regioni_ponti_50m`).
* Argomento 2: `mat11_lines.json`, le linee dei muri bloccate. Se una delle 5 breakline fosse fra queste, lo script si ferma.
* Argomento 3: il percorso del payload da scrivere.

## Output

* Il payload `{"bl": {fid: [[x, y], ...]}}`.
* A schermo: le modifiche e i controlli di accettazione.

## Uso

```bash
~/anaconda3/bin/python3 scripts/fix_bridges.py layers WD/mat11_lines.json WD/write_bridges.json
```

```bash
/usr/bin/python3 scripts/write3.py WD/write_bridges.json 20261119b
```

## Funzionamento

* Un vertice della breakline a meno di 10⁻⁶ m dalla nodestring si considera sulla nodestring. Questi vertici devono essere consecutivi.
* Se sono più di uno, o non coincidono con un estremo, vengono sostituiti dai vertici della nodestring, nello stesso verso della breakline.
* Se c'è un solo vertice vicino a un estremo della nodestring, viene portato esattamente su quell'estremo (caso della 1124).

## Controlli di accettazione

1. Lo spostamento massimo (distanza di Hausdorff) è inferiore a 10⁻⁶ m.
2. Nessuna breakline perde un vertice coincidente con un vertice di una nodestring.
3. Sono elencati i vertici tolti che erano condivisi con altre breakline. Queste diventano innesti a T.
4. Non nascono nuovi incroci.
5. Nessun punto regione si avvicina alle linee.

## Esito del 2026-11-19

* Spostamento massimo: 3.5·10⁻¹⁰ m.
* Un solo vertice condiviso: quello della 1113 dove arrivano la 567 e la 1050, che ora stanno a 5·10⁻¹¹ m dal tratto.
* Nessun nuovo incrocio e nessun punto regione più vicino alle linee.
* Dopo la scrittura: 906 facce senza strisce (`check_regions.py`, `verify3.py`).

## Limiti

* Le coppie breakline–nodestring sono fisse nel codice (`PAIRS`).
