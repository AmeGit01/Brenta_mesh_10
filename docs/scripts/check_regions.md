# check_regions.py

Quinto passo (2026-11-19). Controlla che `regioni_ponti_50m.gpkg` si possa usare direttamente come layer dei punti regione in BASEmesh. Il grafo planare si costruisce con un metodo diverso da quello di `verify3.py`, quindi i due script si controllano a vicenda. Non scrive nulla.

## Requisiti

* Interprete: `python3` di Anaconda (geopandas, shapely 2.1, numpy).

## Input

* Argomento 1, facoltativo: la cartella dei layer (predefinita `/home/amedeo/Documents/Brenta_mesh_10/layers`).
* `regioni_ponti_50m.gpkg`, `breaklines_50m.gpkg` e `boundary_50m.gpkg`.
* L'originale `regioni_ponti.gpkg`, per confrontare i punti con `buco`.

## Output

Solo stampa: un elenco numerato, con `OK` o `**CHECK**` per ogni controllo.

## Uso

```bash
~/anaconda3/bin/python3 scripts/check_regions.py
```

## I controlli

1. **Struttura del layer:** tipo `Point`, EPSG:25832, nessuna Z, nessuna geometria nulla, vuota o non valida.
2. **Punti coincidenti** (entro 0.1 mm).
3. **Attributi:**
   * nessun `nome`, `mat_id` o `max_area` nullo;
   * `max_area` > 0;
   * un solo `mat_id` per nome.

   Stampa anche i `mat_id` condivisi da più nomi, che sono ammessi.
4. **Nomi con più `max_area`:** solo informativo (`sponda_antro`, come negli originali).
5. **Punti con `buco`:** stessi fid e posizioni degli originali (sono i 20 punti dei ponti, del pilone e del sottopasso, che BASEmesh tratta come buchi).
6. **Innesti a T:** conta le estremità che distano meno di 1 mm da un'altra linea senza toccarla. Ognuna viene collegata con `shapely.snap`, che la inserisce come vertice nella linea che tocca (regola del §4).
7. **Grafo planare:**
   * `shapely.node` sulle linee;
   * scomposizione in segmenti con coordinate arrotondate a 10⁻⁷ m;
   * eliminazione dei doppioni, cioè dei tratti sovrapposti (B00400 su `idrometro_Borgo`, breakline 987 e 1225 sulle sezioni);
   * `polygonize_full`.
8. **Punti fuori da ogni faccia, o in più facce.**
9. **Facce senza punto:** distingue le facce vere dalle **strisce** larghe meno di 1 mm (raggio del cerchio inscritto < 1 mm), che nascono da due linee quasi coincidenti.
10. **Facce con più di un punto:** indica se gli attributi coincidono.
11. e 12. **Robustezza:** ripete il grafo dopo aver arrotondato le coordinate delle linee a 1 mm e a 1 cm, come fa un generatore di mesh che fonde vertici vicini. Nessun punto deve cambiare compagni di faccia, e nessuna faccia senza punto può superare 1 m².
13. **Punti a meno di 1 m da una linea.**
14. e 15. **Facce più piccole e più strette:** solo informativo.

## Esito al 2026-11-19

* 906 punti, 911 facce: 906 con un punto ciascuna e 5 strisce sub-micrometriche alle chiusure dei ponti P13, P17, P20 e P27. 206 innesti a T collegati.
* Dopo `fix_bridges.py`: 906 facce, nessuna striscia, 199 innesti a T.
* Nessun cambiamento dopo l'arrotondamento a 1 mm e a 1 cm.
* 26 punti a meno di 1 m da una linea, tutti originali, nelle strisce dei muri e del pilone; il minimo è 0.35 m.

## Limiti

* Il grafo si basa sulla regola del §4: estremità collegate entro 1 mm e nodestring considerate come linee. Non riproduce esattamente il codice di BASEmesh.
* Le strisce si riconoscono solo dalla larghezza (< 1 mm), non dalla loro origine.
