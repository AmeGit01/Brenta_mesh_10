# Brenta: regole e metodo

Sintesi di tutte le informazioni e le regole usate, e da usare, per le azioni registrate in [workflow.md](workflow.md), comprese le decisioni prese dall'utente.

## 1. Regole di lavoro

1. **Ruolo:** costruzione di mesh 2D non strutturate per **BASEMENT v3** (ETH Zurich) con **BASEmesh** in QGIS.
2. **Cartelle:** si lavora solo in `layers/` (dati), `docs/` (documenti) e `scripts/` (codice). Non si toccano mesh (`mesh/`), file modello (`model_*.json`) o progetto QGIS. Se serve cambiarli, si prepara uno snippet o le istruzioni per l'utente.
3. **Originali intoccabili:** i layer originali di `layers/` non si modificano. Ogni risultato va in un **nuovo file** con suffisso (`_50m`), e lo SHA-256 degli originali si verifica a fine lavoro.
4. **Operazioni sostanziali:** prima si espongono metodo, modifiche proposte e domande aperte, poi si chiede conferma. Dopo il lavoro si registrano decisioni ed esito.
5. **Backup:** se si dovesse scrivere su un layer esistente, prima si fa una copia datata (`<layer>_backup_AAAAMMGG.gpkg`) verificata con SHA-256. L'utente deve chiudere il layer in QGIS mentre viene scritto.
6. **Verifiche:** tutte sui file **riletti dal disco**, con codice separato da quello che li ha prodotti, e riportate come elenco numerato con esito.
7. **Registro:** ogni azione utile al workflow va in `docs/workflow.md`. Le operazioni di gestione (rinominare o spostare file) non si registrano.
8. **Script:** ogni script va in `scripts/` (quelli esplorativi in `scripts/esplorativi/`), con commenti in inglese nel codice e una scheda in italiano in `docs/scripts/<nome>.md` (requisiti, input, output, parametri, uso, funzionamento, verifiche e limiti). L'indice e l'ordine di esecuzione sono in `docs/scripts/README.md`.
9. **Lingua:** l'utente scrive in italiano; i nomi dei campi dei layer sono in italiano.
10. **Azioni distruttive:** solo con l'approvazione esplicita dell'utente.

## 2. Progetto e dati

* **Modello:** modello idrodinamico 2D del fiume **Brenta**, CRS **EPSG:25832**.
* **Estensione:** l'intero modello di circa 34 km, da `BC_caldonazzo` a `BC_brenta_valle`, con il Brenta vecchio.
* **Nomi dei campi:** `nome`, `sezione`, `sx` = sinistra orografica, `dx` = destra orografica, `ciglio` = ciglio di sponda, `piede` = piede di sponda.
* **Materiali:** 29 combinazioni `nome`/`mat_id`/`max_area`; quelle valide sono gli attributi dei punti in `regioni_ponti.gpkg`.
* **DTM:** `layers/DTM_finale.tif`, 0.25 m, DEFLATE, nodata −9999. Si usa il **valore della cella** (come *Identify* in QGIS), mai interpolato.

### 2.1 Layer in `layers/`

| File | Stato | Contenuto |
|---|---|---|
| `breaklines.gpkg` | originale | 1285 feature, cigli non allargati; 14 righe con geometria vuota o nulla |
| `boundary.gpkg` | originale | 53 nodestring (BC, ponti P13/P17/P20/P27, Bordignon, Filippini, edifici di Borgo, divergenza, boale…); nessuna sezione |
| `regioni_ponti.gpkg` | originale | 176 punti; fid 65 e 135 con geometria nulla; faccia con 2 punti (fid 57, 58, `muro`) |
| `quote_fisse.gpkg`, `punti_quote_fisse.gpkg`, `quote_fisse_elevation-mesh.2dm` | originali | non usati |
| `centerline_50m.gpkg` | nuovo | `asta_principale` 33 981.6 m, `brenta_vecchio` 3 058.7 m |
| `centerpoints_50m.gpkg` | nuovo | 737 punti: `nome`, `stream`, `s_m`, `dist_next` |
| `bankpoints_50m.gpkg` | nuovo | 1474 punti: `nome`, `sezione`, `s_m`, `z_dtm`, `dist_cp`, `tipo`, `regola`, `prom` |
| `breaklines_50m.gpkg` | nuovo | breakline con i cigli allargati (272 feature modificate) |
| `boundary_50m.gpkg` | nuovo | 53 nodestring + 737 sezioni |
| `regioni_ponti_50m.gpkg` | nuovo | 908 righe (906 con geometria) |

La tabella delle sezioni è in `docs/Brenta_sections_50m_mesh10.csv`.

## 3. Convenzioni BASEmesh

1. **Nomi delle nodestring univoci:** BASEmesh sovrascrive i duplicati senza avvisare.
2. **Geometria:** MultiLineStringZM a **una sola parte**, Z = M = 0. I nodi sono ordinati per distanza dal primo vertice, quindi una stringa a più parti mescolerebbe i nodi.
3. **Verso:** le sezioni si disegnano da sinistra a destra orografica (`upstream_direction: "right"` in BASEMENT).
4. **Nodi condivisi:** un nodo entro la tolleranza di due stringhe compare in entrambe.
5. **Regioni:** esattamente **un punto regione per ogni faccia** del grafo planare (breakline + boundary). Una faccia senza punto resta senza attributi.
6. **Grafo planare:** si ricostruisce con codice proprio, nodando le estremità che toccano un'altra linea entro 1e-3 m, per prevedere le facce prima di scrivere. Sui layer originali dà 173 facce.
7. **Dopo ogni modifica:** la mesh va rigenerata in QGIS e `STRINGDEF` in `model_*.json` va aggiornato con i nomi delle nodestring.

## 4. Centerline e progressive

1. **Asta principale:** scheletro di Voronoi del poligono d'alveo, percorso `BC_caldonazzo` → `BC_brenta_valle` con costo che favorisce il centro del letto.
   * Nel poligono d'alveo si tengono i buchi > 1000 m²; riempirli fa collassare i rami.
   * Tra E 677880 e 678420 l'asta segue il collegamento nord; il meandro sud resta senza sezioni.
2. **Brenta vecchio:** dalla `divergenza_valle_brenta_vecchio` alla confluenza (E ≈ 689850), con punti di passaggio sul letto largo. Esclude la striscia parallela del boale e il collegamento `boale_sifone`.
3. **Lisciatura:** gaussiana con σ di 6 m dove il bed è stretto e di 60 m dove è largo.
4. **Progressiva:** s = 0 all'inizio di ogni ramo, misurata lungo la centerline lisciata.

## 5. Allargamento dei cigli di sponda

Si spostano solo le linee di ciglio (confine `sponda` | `intermedio`). Le linee di piede (bed) non si toccano.

1. **Misura:** la larghezza W tra i cigli si misura ogni 1 m perpendicolarmente alla centerline.
2. **Criterio:**
   * **a monte di Borgo e sul Brenta vecchio:** bed + 2 sponde ≥ **40.10 m**. Dove W < 40.10 m, ogni ciglio si sposta verso l'esterno di (40.10 − W)/2, simmetrico. Il margine di 0.10 m compensa la semplificazione;
   * **a valle di Borgo (s > 17 335 m):** il corridoio è già 50–220 m. Ogni sponda deve essere almeno **16.05 m**, cioè (40.10 − 8.1)/2 con 8.1 m bed mediano del tratto di riferimento (s = 4.2–10.2 km). Lo spostamento si calcola lato per lato;
   * **mai spostare** sponde `sponda_antro` o muri (Borgo);
   * il ciglio resta sempre **≥ 5 m** dalla linea successiva verso l'esterno.
3. **Semplificazione:** le nuove linee si semplificano con tolleranza di 2 cm e si fondono i vertici a meno di 2 m. Gli spostamenti < 1e-6 m si ignorano, per non introdurre scarti numerici.
4. **Struttura da mantenere:**
   * fid e continuità di ogni catena di ciglio;
   * le estremità dei cigli scorrono sul contorno del dominio o su linee non spostate;
   * le linee trasversali che terminano sui cigli (ponti) si prolungano in linea retta fino ai nuovi cigli;
   * una nodestring senza breakline coincidente che chiudeva una regione si prolunga collinearmente (per esempio `idrometro_Ponte_Zaccon`, 0.86 e 0.80 m);
   * nelle giunzioni a T si forzano i vertici, per evitare micro-facce.
5. **Controllo:** il grafo planare deve avere le stesse facce dell'originale, senza micro-facce né fusioni di regioni.

## 6. Sezioni trasversali

1. **Spaziatura:** **50 m ± 0.5 m** lungo la centerline. Si controlla anche la distanza in linea retta tra centerpoint consecutivi.
2. **Direzione:** perpendicolare alla corda della centerline tra s − 1 m e s + 1 m.
3. **Geometria:** segmento retto a **2 vertici**, dal bankpoint `sx` al bankpoint `dx`, con le coordinate copiate esattamente dai bankpoint.
4. **Posizione:** candidati ogni 0.25 m e ottimizzazione su tutta la catena (programmazione dinamica), con queste priorità:
   1. non incrociare nodestring o linee trasversali;
   2. ridurre le violazioni della regola dei 5 m (§8);
   3. restare vicino a 50 m.

   Il vincolo di corda è una penalità, non un vincolo rigido. Sul Brenta vecchio anche le sezioni dell'asta sono ostacoli.
5. **Nomi:** progressiva reale in metri a 5 cifre: `S00050`…`S33940` per l'asta, `V00050`…`V03058` per il Brenta vecchio. Non si usa la progressiva nominale, che si scosterebbe fino a 140 m.
6. **id e fid:** le nuove feature continuano la sequenza; quelle esistenti mantengono fid, id e nome.
7. **Esito atteso:** ogni sezione attraversa solo le due linee di piede, quindi divide solo il bed. Fa eccezione la sezione contro un muro, che si ferma 0.5 m prima e attraversa una sola linea.

## 7. Bankpoint

1. **Profilo:** lungo la sezione, dal piede di sponda verso l'esterno. Si visita ogni cella del DTM attraversata (attraversamento esatto) e se ne usa il valore, senza interpolazione.
2. **Massimo locale:** deve stare almeno **5 cm** sopra il terreno più basso che lo separa da terreno più alto (prominenza). I plateau contano come un solo massimo.
3. **Esclusione:** si ignorano i massimi nella metà inferiore della sponda, cioè sotto z_piede + 0.5·(z_max_sponda − z_piede).
4. **Scelta:** il **primo** massimo valido a partire dal canale.
5. **Fallback:** se non c'è un massimo valido, la **cella più alta** nell'intervallo di ricerca.
6. **Intervallo di ricerca:**
   * da ≥ 5 m dentro il ciglio, con ciglio quello allargato;
   * fino a ≤ 15 m dalla mezzeria della larghezza tra i cigli, quindi i due bankpoint distano al massimo 30 m.
7. **Tratti larghi:** dove il bed supera 30 m, il limite diventa **15 m verso l'esterno da ciascun piede**, sempre entro i 5 m dal ciglio. Lo stesso limite vale dove la mezzeria lascerebbe meno di 2 m di ricerca oltre il piede, per esempio alle confluenze.
8. **Ostacoli:** la ricerca si ferma 0.5 m prima di nodestring, linee interne (edifici di Borgo) o un altro letto vicino.
9. **Posizione:** a metà del tratto di sezione dentro la cella vincente. Se quella cella contiene l'intersezione con il ciglio, il punto va esattamente sull'intersezione.
10. **Attributi:**
    * `nome` = `<sezione>_sx` o `_dx`;
    * `z_dtm` = valore della cella;
    * `dist_cp` = distanza in pianta dal centerpoint;
    * `tipo` (massimo o fallback), `regola` (limite applicato), `prom` (prominenza).

## 8. Regola dei 5 m

* **Regola:** nessun vertice di breakline tra 0 e 5 m da un punto in cui una sezione incrocia una breakline.
* **Gestione:** le linee di piede non si modificano e le violazioni si riportano soltanto. Si cerca solo di ridurle con la posizione delle sezioni. Spostare il vertice esattamente sull'incrocio è la correzione possibile, ma va decisa dall'utente.
* **Rischio:** con un vertice a meno di 0.5 m dall'incrocio si generano elementi molto piccoli. Va controllato dopo la generazione della mesh.

## 9. Punti regione

1. **Un solo punto per faccia** del grafo planare finale.
2. **Quando le regioni si fondono:** si tiene il punto originale, se presente; altrimenti quello con fid più basso.
3. **Distanza dalle linee:** il punto tenuto deve stare **≥ 1 m** da ogni linea; se non ci riesce, si prende un altro candidato.
4. **Nessuna modifica ai punti tenuti:** non si spostano e i loro attributi non cambiano.
5. **Nuove facce di bed:** create dalle sezioni, prendono un nuovo punto nel punto più lontano dai bordi, con gli attributi della regione d'alveo a cui appartengono.
6. **Sostituzione:** un punto esistente a meno di 1 m da una nuova sezione viene sostituito da un punto nuovo nella stessa regione (per esempio il fid 41).
7. **Dati preesistenti:** i punti con geometria nulla e la faccia con 2 punti già presenti all'origine restano come sono.

## 10. Scrittura dei GeoPackage

* **Strumento:** GDAL/OGR (`/usr/bin/python3`), mantenendo tipo di geometria, SRS, campi e indice spaziale dell'originale.
* **Senza GDAL:** si scrive con SQLite in una transazione. Bisogna aggiornare header binario GPKG ed envelope, R-tree, extent in `gpkg_contents` e conteggio in `gpkg_ogr_contents`.
* **Ambiente:**
  * Python di Anaconda: geopandas, shapely 2.1, numpy, scipy, networkx;
  * Python di sistema: GDAL/OGR e PyQGIS, senza shapely.

## 11. Verifiche standard

Da eseguire dopo ogni modifica, sui file riletti dal disco:

1. numero di feature;
2. nomi e id univoci;
3. tipo di geometria, SRS e campi invariati;
4. `PRAGMA integrity_check` = ok, numero di voci nell'R-tree = numero di geometrie non nulle;
5. feature non toccate identiche all'originale;
6. spaziatura lungo la centerline e in linea retta;
7. sezioni perpendicolari, a 2 vertici, primo vertice a sinistra, vertici uguali ai bankpoint;
8. nessun incrocio tra sezioni o con altre nodestring;
9. linee attraversate da ogni sezione;
10. un punto per faccia, senza conflitti di attributi;
11. `z_dtm` uguale al valore della cella DTM, bankpoint ≥ 5 m dal ciglio;
12. bankpoint ricalcolati in modo indipendente;
13. larghezza dopo l'allargamento, campionata ogni 0.5 m;
14. regola dei 5 m;
15. SHA-256 dei layer originali invariato.

## 12. Problemi noti nei dati

* `breaklines.gpkg`: 14 righe con geometria vuota o nulla.
* `regioni_ponti.gpkg`: fid 65 e 135 con geometria nulla; faccia con 2 punti (fid 57, 58).

## 13. Punti aperti (al 16 novembre 2026)

1. **Regola dei 5 m:** 266 attraversamenti su 1470, in 182 sezioni, hanno un vertice a meno di 5 m; 40 sono sotto 0.5 m (minimo 0.018 m a S12654).
2. **Spaziatura in linea retta:** 4 coppie fuori da 50 ± 0.5 m. Partono da s = 1914 (46.68 m), 16180 e 16231 sull'asta, e da 3008 sul Brenta vecchio.
3. **Punti regione vicini alle linee:** 3 nuovi punti a meno di 1 m da una linea (fid 485, 504, 568).
4. **Allargamento incompleto:** sul Brenta vecchio la larghezza resta < 40 m tra s = 2731 e 2910 (sponde urbane, minimo 31 m).
5. **Bankpoint non confermati:** 2 bankpoint (S09338 sx, S30831 dx) non coincidono con il controllo indipendente a 1 cm, per una causa probabile ma non dimostrata.
6. **Mesh e modello:** la mesh va rigenerata da `breaklines_50m`, `boundary_50m` e `regioni_ponti_50m`, poi `STRINGDEF` va aggiornato con le 737 sezioni.
7. **Dopo la mesh:** controllare la qualità degli elementi intorno ai bankpoint, alle violazioni dei 5 m e ai cigli allargati, e che i matID corrispondano alle regioni.

## 14. Storia del metodo

| Data | Passo | Stato |
|---|---|---|
| 28 ottobre 2026 | Sezioni ogni 200 m a tutta valle, `S0200…S6000` | superato |
| 2 novembre 2026 | Sezioni divise in alveo (`S****`) e laterali (`_sx`, `_dx`) | superato |
| 5 novembre 2026 | Bankpoint, sezioni a 2 nodi, cigli allargati a 40 m, regola dei 5 m | metodo valido |
| 9 novembre 2026 | Sezioni a 50 m sul tratto di 6 km, regioni per le nuove facce | metodo valido |
| 9 novembre 2026 | Metodo applicato a 34 km + Brenta vecchio | stato attuale, vedi `workflow.md` |
