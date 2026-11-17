# Workflow: registro delle azioni

Progetto: `/home/amedeo/Documents/Brenta_mesh_10`. Richiesta: replicare il lavoro descritto in `docs/` con sezioni ogni 50 m ± 0.5 m, a partire da `layers/`.

* Regole e metodo applicati: [Brenta_regole_e_metodo.md](Brenta_regole_e_metodo.md).
* Script usati: `scripts/`, documentati in [scripts/README.md](scripts/README.md).
* Qui si registrano solo le azioni utili al workflow, non le operazioni di gestione dei file.

## Registro

### 2026-11-09: lettura documenti e inventario (sola lettura)

1. Letti i 4 documenti in `docs/`: `CLAUDE_CODE_HANDOFF_Brenta.md`, `Brenta_nodestrings_split_report.md`, `Brenta_bankpoints_report.md`, `Brenta_sections_50m_report.md`.
2. Inventario di `layers/` (metadati e attributi, nessuna modifica). **Lo stato trovato non coincide con quello descritto nei report:**

| Voce | Report (`Test_Brenta`, ~6 km) | Trovato in `layers/` |
|---|---|---|
| Estensione | ~6 km, E 679780–684663 | ~30 km, E 675836–705405 |
| `boundary.gpkg` | 34 feature (`P17_*`, `BC_monte/valle`, `S****`) | 53 feature (BC, ponti P13/P17/P20/P27, Bordignon, Filippini, edifici Borgo, divergenza, boale...) e nessuna sezione `S****` |
| `regioni_ponti.gpkg` | 44 punti | 176 punti, 29 combinazioni nome/mat_id/max_area |
| `breaklines.gpkg` | linee ciglio già allargate a 40 m | 1285 feature, stato da verificare |
| `centerline`, `centerpoints`, `bankpoints` | presenti | **assenti** |
| `DTM_finale_clip.tif` | presente | assente, solo `DTM_finale.tif` (0.25 m, DEFLATE, nodata −9999) |
| Altro | | `quote_fisse.gpkg`, `punti_quote_fisse.gpkg`, `quote_fisse_elevation-mesh.2dm` |

3. Strumenti disponibili: GDAL CLI, `/usr/bin/python3` con GDAL/PyQGIS, Python Anaconda con geopandas, shapely 2.1.2, numpy.

### 2026-11-09: analisi preliminare del dominio (sola lettura, script nello scratchpad)

4. Copiati `boundary`, `breaklines`, `regioni_ponti` nello scratchpad, per non interferire con QGIS. I file in `layers/` non sono stati modificati.
5. Ricostruito il grafo planare (`breaklines` + `boundary`): **173 facce**, nessuna senza punto regione, una con 2 punti, e 2 punti (fid 65, 135) fuori da ogni faccia. `breaklines` ha 14 righe con geometria vuota o nulla.
6. Ricostruito lo scheletro (Voronoi) del poligono d'alveo, che risulta connesso, e misurati i percorsi. Sono misure di analisi, non ancora una centerline definitiva.

| Ramo | Lunghezza |
|---|---|
| Asta principale, `BC_caldonazzo` → `BC_brenta_valle` | 34.1 km (~682 sezioni a 50 m) |
| Rami laterali (17) | 9.1 km in totale, da 30 m a 1.7 km ciascuno |

| Tratto dell'asta | Progressiva s (km) | Corridoio bed + sponda: p5 / mediana / p95 (m) | Bed: mediana (m) | Quota < 40 m |
|---|---|---|---|---|
| Caldonazzo–P13 | 0–3.9 | 25.9 / 30.6 / 52.5 | 5.2 | 78 % |
| Tratto dei report (ex `Test_Brenta`) | 4.2–10.2 | 28.2 / 31.7 / 39.2 | 8.1 | 99 % |
| P20–divergenza | 10.2–13.2 | 33.8 / 40.1 / 42.1 | 9.1 | 48 % |
| Borgo (divergenza–confluenza) | 13.2–17.3 | 49.8 / 58.4 / 70.8 | 9.4 | 2 % |
| A valle di Borgo | 17.3–22.8 | 50.2 / 66.5 / 141.1 | 15.6 | 0 % |
| Valle | 22.8–34.1 | 77.9 / 100.4 / 219.4 | 29.3 | 0 % |

**Conclusioni:**

* `layers/` è lo stato **precedente** all'allargamento a 40 m: nel tratto dei report la mediana è 31.7 m, come il valore "prima" di `Brenta_bankpoints_report.md` §7.1. Le linee di ciglio andrebbero quindi ancora allargate.
* La regola dei bankpoint (§7.2, "≤ 15 m dalla mezzeria") vale solo per un corridoio di circa 40 m. Dove il bed supera 30 m (~6.4 km dell'asta) il piede di sponda è già oltre i 15 m, quindi la regola non è applicabile così com'è.
* Il corridoio è < 40 m su ~10.8 km dell'asta, quasi tutti a monte di Borgo.
* Serve una centerline nuova: `layers/` non ne contiene una.

**Stato:** nessun layer creato o modificato. In attesa delle decisioni dell'utente su estensione, allargamento a 40 m e regola bankpoint nei tratti larghi.

### 2026-11-09: decisioni dell'utente

7. **Estensione:** asta principale + Brenta vecchio.
8. **Allargamento a 40 m:** da fare in un **nuovo file**, senza toccare `breaklines.gpkg`. Dopo Borgo il fiume si allarga molto, quindi il criterio va adattato.
9. **Bankpoint nei tratti con bed > 30 m:** ricerca fino a 15 m verso l'esterno da ciascun piede sponda, sempre entro il limite di 5 m dal ciglio.

### 2026-11-09: tracciato delle centerline (scratchpad)

10. Asta principale: scheletro Voronoi del poligono d'alveo, percorso `BC_caldonazzo` → `BC_brenta_valle` con costo che preferisce il centro del letto. Lunghezza dopo lisciatura 33 981.6 m.
11. Brenta vecchio: dalla `divergenza_valle_brenta_vecchio` fino alla confluenza a E ≈ 689850, con punti di passaggio sul letto largo. Lunghezza 3 058.7 m. Il percorso esclude la striscia parallela del boale e il collegamento `boale_sifone`.
12. Lisciatura gaussiana con σ variabile: 6 m dove il bed è stretto, 60 m dove è largo.
13. **Assunzione a monte:** tra E 677880 e E 678420 l'alveo ha due rami. L'asta usa il collegamento nord (bed mediano 7.4 m) e non il meandro sud (4.9 m). Il meandro resta senza sezioni.

### 2026-11-09: allargamento dei cigli (calcolo in scratchpad, file non ancora scritto)

14. **Criterio adottato**, derivato dal §7.1 dei report e adattato a valle di Borgo:
    * **A monte di Borgo e sul Brenta vecchio:** come §7.1, W = bed + 2 sponde ≥ 40.10 m. Spostamento simmetrico (40.10 − W)/2 per lato.
    * **A valle di Borgo (s > 17 335 m):** il valore fisso di 40 m non ha significato, perché il corridoio è già 50–220 m. Ogni sponda deve essere larga almeno **16.05 m**, la larghezza media per lato nel tratto di riferimento ((40.10 − 8.1)/2). Lo spostamento è calcolato lato per lato.
    * **Borgo:** nessuno spostamento dove la sponda è `sponda_antro` o muro.
    * Il ciglio resta sempre ad almeno 5 m dalla linea successiva verso l'esterno.
15. Linee traversali che finivano sui cigli (ponti P13, P17, P20: fid 1113–1116, 1421, 1422) prolungate in linea retta fino ai nuovi cigli. Estremi di ciglio fatti scorrere sul contorno o su linee non spostate: fid 17, 1001, 1061.
16. Nodestring `idrometro_Ponte_Zaccon` prolungata collinearmente sui due estremi (0.86 e 0.80 m), altrimenti la sponda perderebbe la chiusura di regione.
17. Verifica del grafo planare dopo lo spostamento: 173 facce come l'originale, nessuna micro-faccia, nessuna fusione di regioni. Resta solo la faccia con 2 punti già presente all'origine (fid 57 e 58, `muro`).

### 2026-11-09: sezioni, bankpoint, regioni e scrittura dei file

18. **Posizione delle sezioni.** Per ogni ramo, candidati ogni 0.25 m lungo la centerline. Ottimizzazione su tutta la catena con passo 49.5–50.5 m lungo la centerline. In ordine di priorità: non incrociare nodestring e linee trasversali, ridurre le violazioni della regola dei 5 m, restare vicino a 50 m. Il Brenta vecchio considera come ostacoli anche le sezioni dell'asta.
19. **Direzione:** perpendicolare alla corda della centerline tra s − 1 m e s + 1 m. Primo vertice in sinistra orografica (`sx`), come nei report.
20. **Bankpoint** con la regola §7.2: primo massimo locale con prominenza ≥ 5 cm, escludendo la metà inferiore della sponda; altrimenti la cella più alta nell'intervallo. Il profilo attraversa ogni cella del DTM senza interpolazione. Il limite di ricerca è ≥ 5 m dentro il ciglio e ≤ 15 m dalla mezzeria.
21. **Limite di 15 m dal piede sponda** (decisione 9) dove il bed supera 30 m. L'ho applicato anche dove la mezzeria spostata (es. alle confluenze) lascerebbe meno di 2 m di ricerca: questa estensione è una mia scelta.
22. **Limitazioni aggiunte alla ricerca:** il bankpoint si ferma 0.5 m prima di nodestring o linee interne (edifici a Borgo) e 0.5 m prima di un altro letto vicino (22 lati, soprattutto Brenta vecchio).
23. **Sezioni contro i muri:** 4 lati (S16382 dx, S16432 dx, S16533 sx, S16583 dx) terminano 0.5 m prima del muro di un edificio, dentro il bed, perché l'edificio coincide con il piede sponda. Su quei lati non attraversano il piede.
24. **Nomi:** progressiva reale in metri, 5 cifre: `S00050`…`S33940` per l'asta, `V00050`…`V03058` per il Brenta vecchio. I report usano invece la progressiva nominale, ma qui lo scarto accumulato sarebbe fino a 140 m. Fid 64–800, id 60–796.
25. **File creati in `layers/`** (nessun originale modificato; SHA-256 di `boundary`, `breaklines`, `regioni_ponti` invariati):

| File | Contenuto |
|---|---|
| `centerline_50m.gpkg` | 2 linee: `asta_principale` (33 981.6 m), `brenta_vecchio` (3 058.7 m) |
| `centerpoints_50m.gpkg` | 737 punti: `nome`, `stream`, `s_m`, `dist_next` |
| `bankpoints_50m.gpkg` | 1474 punti: `nome`, `sezione`, `s_m`, `z_dtm`, `dist_cp`, `tipo`, `regola`, `prom` |
| `breaklines_50m.gpkg` | Copia di `breaklines` con 272 feature modificate (cigli allargati e linee collegate) |
| `boundary_50m.gpkg` | 53 nodestring originali (52 identiche, `idrometro_Ponte_Zaccon` prolungata) + 737 sezioni |
| `regioni_ponti_50m.gpkg` | 908 righe, di cui 906 con geometria |

26. Creato anche `docs/Brenta_sections_50m_mesh10.csv`: tabella delle 737 sezioni con quote, tipo, regola, prominenza e lunghezza.
27. **Regioni:** sulle 905 facce finali, 733 nuovi punti con gli attributi della regione d'alveo di appartenenza. Il punto originale fid 41 (`source_3_brenta_3`, a 0.04 m da una nuova sezione) è sostituito; tutti gli altri restano. I fid 65 e 135 hanno geometria nulla già all'origine e restano così.

### 2026-11-09: verifiche (sui file riletti dal disco, con codice separato)

1. Conteggi: `breaklines_50m` 1285, `boundary_50m` 790 (53 + 737), `regioni_ponti_50m` 908, `centerpoints_50m` 737, `bankpoints_50m` 1474. **OK**
2. Nomi e id delle sezioni univoci. **OK**
3. Tipo geometria e SRS (EPSG:25832) invariati, `integrity_check` ok, R-tree = feature con geometria. **OK**
4. Feature non toccate identiche all'originale: 999 breakline, 52 nodestring, 173 punti regione. **OK**
5. Passo lungo la centerline: asta 49.75–50.50 m, Vecchio 49.50–50.50 m. **OK**, nessuna fuori tolleranza.
6. Distanza rettilinea tra centerpoint: **4 coppie fuori da 50 ± 0.5 m**, in curve strette o rami con punte: partenze a s = 1914 (46.68 m), 16180 (48.05 m), 16231 (49.31 m) sull'asta e 3008 (48.73 m) sul Vecchio.
7. Sezioni perpendicolari alla corda (scarto ≤ 6.5e-9°), 2 vertici, primo vertice a sinistra, vertici uguali ai bankpoint. **OK**
8. Nessun incrocio tra sezioni, né con le altre nodestring. **OK**
9. Linee d'alveo attraversate: 733 sezioni attraversano esattamente 2 linee, le 4 contro i muri 1 sola. **OK**
10. Grafo planare finale: 905 facce, ognuna con un punto, più la faccia con 2 punti già presente all'origine (fid 57, 58). **OK**
11. `z_dtm` uguale al valore della cella DTM sui 1474 punti; bankpoint a ≥ 5 m dal ciglio. **OK**
12. Rideterminazione indipendente dei bankpoint con campionamento a 1 cm: 1446 su 1474 uguali. Le 28 differenze sono 26 celle attraversate per meno di 1 cm (il campionamento non le vede) e 2 casi con massimo diverso (S09338 sx, S30831 dx). Questi 2 sono probabilmente dovuti alla stessa causa, che però **non ho dimostrato**.
13. Allargamento, campioni ogni 0.5 m, sui file finali:
    * Asta a monte di Borgo: W < 40 m solo sullo 0.17 % dei campioni (59 su 34 669), in punti isolati e in testa all'asta (minimo 34.4 m a s = 1–2 m).
    * Asta a valle di Borgo: sponda < 16 m solo in punti isolati e all'ultimo tratto, s = 33 957–33 980, dove il corridoio arriva all'uscita (nessuna sezione lì).
    * Brenta vecchio: W < 40 m su 397 campioni su 6112, tra cui s = 2731–2910 (sponde urbane non spostate, minimo 31 m) e s = 1090–1104.
    * I cigli spostati non si autointersecano. Le 11 linee trasversali che risultano incrociare altre linee sono i tagli dei ponti sui piedi sponda, già presenti in origine: 10 coppie già in `breaklines.gpkg`, 1 che tocca un vertice.

### Punti aperti

* **Regola dei 5 m non risolta:** 266 attraversamenti su 1470, in 182 sezioni, hanno un vertice di breakline a meno di 5 m. 40 sono sotto 0.5 m (minimo 0.018 m, S12654) e possono generare elementi molto piccoli. Come deciso nel report dei 50 m, le linee di piede non sono state modificate.
* **3 nuovi punti regione a meno di 1 m da una linea:** fid 485 (0.14 m), 504 (0.19 m), 568 (0.69 m), in regioni troppo strette per rispettare il limite.
* **Prova di riproduzione del report non eseguita:** in `layers/` mancano le sezioni e la centerline originali, quindi non ho potuto confrontare il metodo con i 60 bankpoint dei report.
* **Mesh non rigenerata:** va fatta in QGIS/BASEmesh da `breaklines_50m`, `boundary_50m`, `regioni_ponti_50m`. `STRINGDEF` deve includere le 737 nuove sezioni.
