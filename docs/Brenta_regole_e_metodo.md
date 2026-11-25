# Brenta: regole e metodo

Questo documento descrive le regole con cui è preparata la geometria della mesh del Brenta e **lo stato attuale** dei dati. Cosa è stato fatto e quando, con numeri e verifiche, è nel registro [workflow.md](workflow.md). La storia del metodo è riassunta al §15.

## 1. Il progetto

Il lavoro riguarda un modello idrodinamico bidimensionale del fiume Brenta, da calcolare con **BASEMENT v3** (ETH Zurigo). La mesh non strutturata si costruisce in QGIS con il plugin **BASEmesh**. Tutti i dati sono nel sistema di riferimento **EPSG:25832**.

Il dominio copre circa 34 km di asta principale, dalla condizione al contorno di monte `BC_caldonazzo` a quella di valle `BC_brenta_valle`, più il Brenta vecchio, che si stacca a Borgo e rientra più a valle.

Le sezioni trasversali sono ogni **50 ± 0.5 m** lungo l'alveo e sono divise in **due rami indipendenti**:

* **V, Brenta vecchio:** dalla **V00000** alla V03000, cioè 61 sezioni. La V00000 è la nodestring della divergenza dall'asta principale.
* **B, asta principale:** da Caldonazzo a valle, dalla **B00000** alla B33800, cioè 677 sezioni. La B00000 è a 23.02 m dal BC di monte. La B16550 coincide con l'idrometro di Borgo.

Ogni sezione va da un punto di sponda (bankpoint) a quello opposto ed è usata in BASEMENT come nodestring di controllo.

## 2. Come si lavora

* **Cartelle:** si lavora soltanto in `layers/` (dati), `docs/` (documentazione) e `scripts/` (codice).
* **File che non si toccano:** la mesh in `mesh/`, i file di modello `model_*.json` e il progetto QGIS. Se un cambiamento li riguarda, si preparano le istruzioni o il testo da incollare, e lo applica l'utente.
* **Layer originali:** non si modificano. I risultati sono nei layer con suffisso `_50m`.
* **Prima di riscrivere un layer `_50m`:**
  * se ne fa una copia con etichetta (`<layer>_backup_AAAAMMGG<lettera>.gpkg`), verificata con SHA-256;
  * l'utente deve aver chiuso il layer in QGIS. Un file `-wal` accanto al layer vuol dire che è ancora aperto.
* **Consenso dell'utente:** prima di un'operazione sostanziale si espongono metodo, modifiche e domande, e si aspetta la conferma. Le cancellazioni richiedono sempre un consenso esplicito.
* **Verifiche:** si fanno sui file **riletti dal disco**, con codice diverso da quello che li ha prodotti. L'esito si riporta come elenco numerato.
* **Registro:** ogni azione utile al flusso di lavoro si annota in `docs/workflow.md`.
* **Script del progetto:** stanno in `scripts/`, con commenti in inglese e una scheda in italiano in `docs/scripts/`.
* **Script della skill:** dal 24 novembre calcoli, scritture e verifiche usano gli script della skill `skills/river-cross-sections/`, con la configurazione [rcs_config_brenta_vb.json](rcs_config_brenta_vb.json). Gli script del progetto che hanno i vecchi rami N/V/B scritti nel codice non valgono per lo stato attuale.

## 3. I dati

### 3.1 Il DTM

Il terreno è descritto da `layers/DTM_finale.tif`: celle di 0.25 m, nodata −9999. Si legge sempre il **valore della cella** che contiene il punto, lo stesso che restituisce lo strumento *Identify* di QGIS. Non si interpola mai.

### 3.2 I layer

I campi hanno nomi italiani. `sx` e `dx` indicano la sinistra e la destra orografica, cioè guardando verso valle. Il ciglio è il bordo superiore della sponda; il piede è quello inferiore, a contatto con il letto.

| File | Origine | Contenuto |
|---|---|---|
| `breaklines.gpkg` | originale | 1285 linee, con i cigli non allargati; 14 righe hanno geometria vuota o nulla. |
| `boundary.gpkg` | originale | 53 nodestring, nessuna sezione. |
| `regioni_ponti.gpkg` | originale | 176 punti regione; i fid 65 e 135 hanno geometria nulla, i fid 57 e 58 cadono nella stessa faccia. |
| `quote_fisse.gpkg`, `punti_quote_fisse.gpkg`, `quote_fisse_elevation-mesh.2dm` | originali | Non usati per le sezioni. |
| `breaklines_50m.gpkg` | derivato | 1288 linee, di cui 22 con geometria vuota o nulla; le 1462 e 1463 sono i muri aggiunti a mano a Borgo. Hanno i cigli allargati e sono corrette per la regola dei nodi vicini (§9). |
| `boundary_50m.gpkg` | derivato | 48 nodestring e 738 sezioni. Le sezioni hanno fid da 64 e id da 60, prima le V (V00050–V03000), poi le B. Fa eccezione la V00000, che è la nodestring della divergenza rinominata e mantiene il fid 22. |
| `regioni_ponti_50m.gpkg` | derivato | 904 punti regione, tutti con geometria, uno per faccia (§10). |
| `centerline_50m.gpkg` | derivato | Due linee d'asse: `V_brenta_vecchio`, dalla V00000 alla confluenza, e `B_caldonazzo_valle`, tutta l'asta con `s0_asta` = 0. |
| `centerpoints_50m.gpkg` | derivato | 738 punti, uno per sezione. `stream` indica il ramo, `s_m` la progressiva reale nel ramo, `dist_next` la distanza dalla sezione successiva. |
| `bankpoints_50m.gpkg` | derivato | 1476 punti, due per sezione (`<sezione>_sx`, `<sezione>_dx`). |

I punti regione portano il nome, il materiale (`mat_id`), l'area massima degli elementi (`max_area`) e il flag `buco`. Le combinazioni di questi valori nei dati originali definiscono i materiali del modello.

La tabella di tutte le sezioni è [Brenta_sections_50m_mesh10.csv](Brenta_sections_50m_mesh10.csv).

## 4. Come ragiona BASEmesh

* **I nomi delle nodestring sono univoci.** Se due stringhe hanno lo stesso nome, BASEmesh tiene l'ultima e scarta l'altra senza avvisare.
* **Ogni nodestring è una linea a una sola parte,** in formato MultiLineStringZM con Z = M = 0. BASEmesh ordina i nodi di una stringa per distanza dal primo vertice, quindi i pezzi di una stringa multipla si mescolerebbero.
* **Le sezioni vanno da sinistra a destra orografica.** In BASEMENT corrisponde a `upstream_direction: "right"`.
* **Ogni faccia del grafo planare ha esattamente un punto regione** (§10).
* **Dopo ogni modifica alla geometria si rigenera la mesh.** Il blocco `STRINGDEF` dei file di modello deve elencare tutte le nodestring con i nomi attuali.

## 5. La linea d'asse

Le sezioni si posizionano lungo una linea d'asse che segue il centro dell'alveo. La progressiva `s` si misura lungo questa linea, da zero all'inizio di ogni ramo.

* **Asta principale (ramo B).** È il percorso dello scheletro di Voronoi del poligono d'alveo che va da `BC_caldonazzo` a `BC_brenta_valle` restando più vicino al centro del letto.
  * Nel poligono si conservano i buchi più grandi di 1000 m².
  * Tra E 677880 e 678420 l'alveo si divide: l'asta segue il collegamento nord, più largo, e il meandro sud resta senza sezioni.
* **Brenta vecchio (ramo V).** Va dalla nodestring della divergenza (V00000) alla confluenza, intorno a E 689850. Il percorso passa per alcuni punti di passaggio, per non deviare nella striscia del boale né nel collegamento `boale_sifone`.
* **Lisciatura.** La linea è lisciata con un filtro gaussiano di ampiezza variabile: 6 m dove il letto è stretto, fino a 60 m dove è largo.

Ogni linea d'asse arriva fino alla fine della sua linea d'origine, non solo fino all'ultima sezione. Così una sezione spostata a mano oltre l'ultima posizione la incrocia comunque.

## 6. L'allargamento delle sponde

Il bankpoint deve stare abbastanza lontano dal ciglio e la sezione deve restare compatta. Per conciliare le due cose letto e sponde devono formare un corridoio abbastanza largo. Dove non lo è, i cigli (il confine tra sponda e fascia intermedia) sono stati spostati verso l'esterno; i piedi restano dove sono.

* **Asta a monte di Borgo** (s ≤ 17 335 m sulla linea d'asse con cui è stato calcolato l'allargamento) **e Brenta vecchio:** il corridoio tra i cigli è largo almeno **40.10 m**, con spostamento simmetrico.
* **A valle di Borgo:** ogni sponda è larga almeno **16.05 m**, sponda per sponda.
* **Linee che non si spostano mai:** sponde urbane (`sponda_antro`) e muri.
* **Distanza dalla linea successiva:** il ciglio spostato resta ad almeno **5 m** da quella verso l'esterno.
* **Topologia:**
  * ogni tratto di ciglio conserva il proprio fid e resta collegato ai vicini;
  * le estremità scorrono lungo le linee su cui terminano;
  * le chiusure dei ponti contengono esattamente i vertici della nodestring del ponte;
  * gli innesti a T hanno un vertice comune.

Il grafo planare ha le stesse facce di prima dell'allargamento.

## 7. Le sezioni

* **Passo:** le sezioni sono distanziate di **50 ± 0.5 m** lungo la linea d'asse. Si controlla anche la distanza in linea retta tra centerpoint consecutivi, che nelle curve strette risulta più corta.
* **Direzione:** ogni sezione è perpendicolare alla corda della linea d'asse tra s − 1 m e s + 1 m.
* **Geometria:** la sezione è un **segmento a due vertici** dal bankpoint sinistro al destro, con i vertici uguali ai bankpoint.
* **Linee incrociate:** una sezione corretta attraversa solo le due linee di piede. Una sezione che incontra un muro coincidente con il piede si ferma 0.5 m prima e attraversa una sola linea; a Borgo alcune sezioni sistemate a mano terminano esattamente su un muro o sulla nodestring di un edificio.
* **Scelta delle posizioni:** si fa su tutto il ramo in una volta, con candidati ogni 0.25 m e programmazione dinamica. Le priorità, in ordine:
  1. non incrociare nodestring o linee trasversali;
  2. ridurre le violazioni della regola dei nodi vicini (§9);
  3. tenere il passo vicino a 50 m.

  La perpendicolarità è una penalità, non un vincolo.
* **Nomi:** lettera del ramo seguita dalla posizione nel ramo moltiplicata per 50, a cinque cifre: `V00000` … `V03000`, `B00000` … `B33800`. Il nome è nominale; la progressiva vera è in `s_m` dei centerpoint. Per esempio la B16000 è a s = 16 102.77 m.
* **Sezione dell'idrometro di Borgo:** la **B16550** coincide esattamente con la nodestring `idrometro_Borgo` (stessi due vertici, il sinistro per primo). È la misura di portata più affidabile del modello. I suoi bankpoint sono gli estremi della nodestring, con `tipo` `nodestring` e `regola` `idrometro_Borgo`.
* **V00000:** è la nodestring della divergenza. I suoi bankpoint sono i due estremi, con `tipo` `nodestring` e `regola` `V00000`; il centerpoint è l'incrocio con la linea d'asse V.
* **Ponti:** nessuna sezione cade dentro un ponte. La B16250 è 20 m a valle del Ponte Bordignon e la B33150 9 m a valle del Ponte Filippini.

## 8. I bankpoint

Il bankpoint è il punto in cui la sezione finisce su ciascuna sponda. È il **primo rilievo significativo** che si incontra salendo dal letto verso l'esterno, non il punto più alto della sponda.

* **Direzione:** la ricerca avviene lungo la sezione, perpendicolare alla linea d'asse.
* **Profilo:** dal piede verso l'esterno si visitano una per una tutte le celle del DTM attraversate dalla sezione.
* **Massimo locale:** conta solo se ha una **prominenza** di almeno 5 cm. Si scartano i massimi nella metà inferiore della sponda, cioè sotto z_piede + 0.5·(z_max − z_piede). Si prende il **primo** massimo valido (`tipo` `max`); se non ce n'è, la cella più alta della finestra (`fallback`).
* **Finestra di ricerca.** Si ferma:
  * almeno **5 m prima del ciglio**, cioè del bordo della fascia intermedia;
  * a non più di **15 m dalla mezzeria** del corridoio (`regola` `mid`). Dove il letto è largo più di 30 m, o la mezzeria lascia meno di 2 m oltre il piede, il limite è invece 15 m dal piede (`toe15`);
  * **0.5 m prima** di una nodestring, di una linea interna o del piede di un altro letto.
* **Posizione:** il bankpoint sta a metà del tratto di sezione nella cella scelta. Se quella cella contiene l'incrocio con il ciglio, il punto va sull'incrocio.
* **Sezioni modificate a mano:** il bankpoint segue il nuovo estremo, con `tipo` e `regola` `manuale` e la quota della cella. Anche il centerpoint si aggiorna come incrocio con la linea d'asse, e con lui `s_m`, `dist_next` e `dist_cp`.
* **Attributi:** `nome`, `sezione`, `s_m`, `z_dtm` (valore della cella), `dist_cp` (distanza dal centerpoint), `tipo`, `regola`, `prom` (la prominenza).

## 9. La regola dei nodi vicini

Dove una sezione incrocia una breakline nasce un nodo della mesh. Se a breve distanza c'è un vertice di breakline, tra i due nodi si formano elementi minuscoli o molto allungati. Per questo **nessun vertice di breakline deve trovarsi a meno di 2 m da un incrocio** con una sezione. I vertici sugli incroci della stessa sezione non contano.

**Come si corregge: si sposta il vertice vicino sull'incrocio** (`snap_near_nodes.py` della skill). Non si crea un vertice nuovo.

* Il vertice vicino della breakline incrociata si porta esattamente sul punto d'incrocio. La sezione continua a incrociare la breakline nello stesso punto, ma ora su un vertice esistente.
* Le linee che condividono quel vertice (nodi, innesti a T) lo seguono, quindi nessun collegamento si perde.
* Altri vertici vicini della stessa breakline si eliminano, se sono vertici interni non condivisi.
* Anche un vertice a una frazione di millimetro dall'incrocio si porta sull'incrocio: altrimenti la mesh avrebbe un lato di quella lunghezza.

Uno spostamento si accetta solo se:
* il vertice non sta su una nodestring o su un'altra sezione;
* non tocca una linea dei muri (`mat_id` 11), che sono bloccate;
* non è l'estremità di un innesto a T;
* le linee restano semplici e non nascono incroci nuovi;
* nessun punto regione cade nell'area spazzata o si avvicina sotto 1 m;
* non nasce un angolo sotto i 30°.

Un vertice vicino che appartiene a **un'altra linea** non si può portare sull'incrocio, perché collegherebbe due linee: si segnala. I casi che non si possono correggere restano violazioni da decidere con l'utente (§14 bis). Il metodo precedente, che inserisce l'incrocio come vertice e toglie o fa scorrere i vertici attorno (`fix_near_nodes.py`), resta disponibile per i casi particolari.

## 10. I punti regione

Breakline e nodestring, comprese le sezioni, dividono il piano in **facce** (il grafo planare). BASEmesh dà a ogni faccia il materiale e l'area massima degli elementi del **punto regione** che vi cade dentro. Quindi:

* una faccia **senza punto** resta senza materiale: i suoi elementi hanno materiale 0 nella mesh;
* una faccia **con due punti** ha attributi ambigui.

Ogni linea nuova o spostata può dividere una faccia in due. Il punto resta in una metà sola e l'altra rimane senza. Per esempio una sezione che va oltre il piede e taglia anche una sponda, un muro o un sottopasso divide anche quella faccia. Per questo dopo ogni modifica si riconta il grafo (`check_regions.py`, `verify3.py`).

Le regole per assegnare i punti:
* in ogni faccia c'è **un solo punto**;
* se due facce si fondono, si tiene il punto originale, se c'è, altrimenti quello con il fid più basso;
* il punto tenuto sta ad almeno 1 m da ogni linea, altrimenti si sceglie un altro candidato;
* un punto originale non si sostituisce mai, nemmeno nelle strisce strette dei muri;
* i punti tenuti non si spostano e non cambiano attributi;
* una faccia nuova riceve un punto nel luogo più lontano dai bordi, con gli attributi della regione da cui deriva. Se quella regione è un buco (ponte, pilone, sottopasso), anche il punto nuovo è un buco;
* i punti regione si cambiano solo nelle facce toccate dalla modifica in corso.

Il controllo vale anche dopo aver arrotondato le coordinate delle linee a 1 mm e a 1 cm, come fa un generatore di mesh che fonde vertici vicini.

## 11. Scrittura dei file e ambiente

I GeoPackage si scrivono con GDAL/OGR (`write3.py` della skill), mantenendo tipo di geometria, sistema di riferimento, campi e indice spaziale.

Ci sono due ambienti Python:
* quello di Anaconda (`~/anaconda3/bin/python3`), con geopandas, shapely 2.1, numpy e scipy;
* quello di sistema (`/usr/bin/python3`), con GDAL/OGR e senza shapely, usato da chi legge il DTM o scrive i GeoPackage.

## 12. Le verifiche

Dopo ogni modifica, sui file riletti dal disco:

1. `verify3.py` controlla:
   * conteggi, nomi e id;
   * geometria e verso delle sezioni;
   * linee d'asse, centerpoint e bankpoint;
   * passo e regola dei nodi vicini rispetto alle eccezioni;
   * incroci;
   * punti regione;
   * integrità dei GeoPackage;
   * angoli.
2. `verify3_dtm.py`: `z_dtm` è uguale al valore della cella.
3. `check_regions.py`: un punto per faccia, anche con le coordinate arrotondate a 1 mm e 1 cm.
4. `sync_cp_bp.py`: dopo un riallineamento deve dare 0 cambiamenti.
5. `check_angles.py`: nessun angolo nuovo sotto i 30° tra linee.
6. `check_mesh.py`: sulla mesh rigenerata controlla data, lati più corti, elementi con materiale 0 e nodestring.
7. A fine lavoro: l'impronta SHA-256 dei layer originali è invariata.

## 13. Difetti noti nei dati originali

* **`breaklines.gpkg`:** 14 righe hanno geometria vuota o nulla.
* **`regioni_ponti.gpkg`:** i fid 65 e 135 hanno geometria nulla, e i fid 57 e 58 cadono nella stessa faccia.

Restano negli originali; in `regioni_ponti_50m` i fid 65, 135 e 58 non ci sono.

## 14. Cosa resta da fare

1. **Mesh e modello:**
   * rigenerare la mesh e controllarla con `check_mesh.py`;
   * aggiornare `STRINGDEF` con i 738 nomi attuali;
   * verificare come BASEmesh e BASEMENT trattano la B16550, che coincide con `idrometro_Borgo`.
2. **B16450:** il suo estremo destro va 1.3 m oltre il muro 893 (è così fin dall'inizio); la nodestring `edificio_paratoie_borgo` parte dal punto in cui la sezione incontra il muro. Da decidere se accorciare la sezione al muro.
3. **Breakline che non coincidono più con una sezione:** la 1225 e la striscia della sorgente 987/988.

Tutte le altre violazioni delle regole sono eccezioni accettate (§14 bis). Restano segnalati dalle verifiche, senza essere violazioni:
* la V00000 mantiene il fid 22, fuori dal blocco delle sezioni;
* il punto originale 30 `sottopasso-borgo` ha attributi diversi dall'originale (materiale 1, nessun `buco`), per scelta dell'utente;
* il punto nuovo 1016 (`bed`) sta a 0.52 m da una linea, in una faccia stretta.

Le nodestring `link_borgo_monte`, `link_borgo_valle`, `check_portata_1` e `check_portata_2` sono state tolte dall'utente; le nodestring sono 48. I punti `sottopasso-borgo` (30 e 1054) hanno materiale 1 e nessun `buco`: il sottopasso non c'è più e l'acqua passa in superficie. Il pilone 61 è di nuovo un buco. Togliendo `check_portata_1` e `check_portata_2` si sono fuse delle facce e sono rimasti punti doppi con gli stessi attributi: si è tenuto quello con il fid più basso (tolti gli originali 66, 67, 73, 74, 75, 76, 77, 78, 87, 88, 91, 92 e i derivati 997, 1003).

## 14 bis. Eccezioni

Accettate dall'utente il 24 novembre 2026, dopo le ultime modifiche a mano. Sono registrate, con il motivo, in `exceptions` di [rcs_config_brenta_vb.json](rcs_config_brenta_vb.json), e le verifiche le confrontano con le violazioni trovate.

**Sezione con più di due vertici:** B16100 (3 vertici, disegnata così dall'utente).

**Regola dei nodi vicini (raggio 2 m):**

| Sezione | Motivo |
|---|---|
| B15950, B16250, B16450 (2 incroci), B16600, B16650 | vertice vicino su una linea bloccata dei muri di Borgo (da 0.87 a 1.42 m; alla B16250 è condiviso con il muro nuovo 1463) |
| B06800 | vertici 562 e 565 (0.66 e 0.51 m) su un'altra nodestring o sezione |
| B08900 | vertici 649 e 650 (1.05 e 0.89 m): spostarli porterebbe via un punto regione o creerebbe un angolo di 7.3° |

**Passo (50 ± 0.5 m, lungo la linea d'asse o in linea retta):**

| Coppia | Motivo |
|---|---|
| V00000–V00050 | 52.36 m: la V00000 è la nodestring della divergenza, fissa |
| V01050–V01100 | 50.517 m: V01050 modificata a mano |
| B01150–B01200 | 50.52 m: B01150 modificata a mano |
| B01900–B01950 | curva stretta, 48.13 m in linea retta; B01900 modificata a mano |
| B02000–B02050 | 50.502 m: B02000 modificata a mano |
| B02100–B02150 | curva stretta dopo l'unione dei rami, 47.32 m in linea retta |
| B02250–B02300 | curva di quasi 90° dopo l'unione dei rami, 42.47 m in linea retta |
| B15900–B15950, B15950–B16000 | 50.52 e 50.50 m: sezioni modificate a mano |
| B16050–B16100 | 49.13 m in linea retta: sezioni di Borgo modificate a mano |
| B16300–B16350 | 50.504 m, tra i muri di Borgo |
| B16400–B16450, B16450–B16500 | 47.1 e 53.6 m: B16450 posata a mano tra i muri di Borgo |
| B16600–B16650 | 50.502 m: B16600 modificata a mano |
| B17050–B17100 | 50.509 m: B17100 modificata a mano |
| B27350–B27400 | curva stretta, 47.85 m in linea retta |

**Angoli sotto i 30°:** breakline 853 e 1126 a Borgo (17.3°); breakline 1367 con la B17900 (27.5°).

Le eccezioni accettate prima dell'unione dei rami (nomi vecchi: `Nxxxxx` → `B(xxxxx − 50)`, `Bxxxxx` → `B(xxxxx + 16150)`) sono superate da questo elenco.

## 15. Come si è arrivati a questo metodo

| Data | Passo |
|---|---|
| 28 ottobre 2026 | Sezioni ogni 200 m estese a tutta la valle (superato) |
| 2 novembre 2026 | Sezioni divise in parte d'alveo e parti laterali (superato) |
| 5 novembre 2026 | Bankpoint, sezioni a due vertici, corridoio di 40 m, regola dei nodi vicini a 5 m |
| 9 novembre 2026 | Sezioni ogni 50 m, prima su 6 km, poi sui 34 km dell'asta e sul Brenta vecchio |
| 17 novembre 2026 | Tre rami N, V, B; correzione delle breakline per la regola dei nodi vicini |
| 18 novembre 2026 | Ramo B spostato di 16.6 m, sezione coincidente con `idrometro_Borgo` |
| 24 novembre 2026 | Due rami V e B: le N spostate di 27.23 m e unite a B, due sezioni nuove, V00000 dalla nodestring della divergenza; regola dei nodi vicini a 2 m, con il vertice vicino spostato sull'incrocio |
