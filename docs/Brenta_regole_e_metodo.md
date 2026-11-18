# Brenta: regole e metodo

Questo documento raccoglie le regole con cui è stata preparata la geometria della mesh del Brenta, e con cui va portato avanti il lavoro. Spiega cosa si fa e perché. Cosa è stato fatto concretamente, con date, numeri e verifiche, è invece nel registro [workflow.md](workflow.md).

## 1. Il progetto

Il lavoro riguarda un modello idrodinamico bidimensionale del fiume Brenta, da calcolare con **BASEMENT v3** (ETH Zurigo). La mesh non strutturata si costruisce in QGIS con il plugin **BASEmesh**. Tutti i dati sono nel sistema di riferimento **EPSG:25832**.

Il dominio copre circa 34 km di asta principale, dalla condizione al contorno di monte `BC_caldonazzo` a quella di valle `BC_brenta_valle`, più il ramo del Brenta vecchio, che si stacca a Borgo e rientra più a valle.

Alla confluenza di Borgo la geometria non è riproducibile da un modello 1D. Per questo le sezioni sono divise in **tre rami indipendenti**, ognuno chiuso da condizioni al contorno nel modello 1D:

* **N:** da Caldonazzo a Borgo, fino alla sezione N16050, che attraversa sia il canale principale sia quello parallelo di destra;
* **V:** il Brenta vecchio, fino alla V03000;
* **B:** da Borgo a valle, a partire dalla B00000. La B00050 sta a monte del Ponte Bordignon.

Nella mesh 2D i tre rami restano collegati. Tra la fine di N e V e l'inizio di B c'è un tratto senza sezioni.

L'obiettivo di questa fase è dotare la mesh di **sezioni trasversali ogni 50 m** (con tolleranza di ± 0.5 m) lungo l'alveo. Ogni sezione va da un punto di sponda a quello opposto ed è usata in BASEMENT come nodestring di controllo. Per arrivarci servono quattro passi: la linea d'asse dell'alveo, l'allargamento delle sponde, i punti di sponda (bankpoint) e i punti regione delle nuove facce.

## 2. Come si lavora

Si lavora soltanto nelle cartelle `layers/` (dati), `docs/` (documentazione) e `scripts/` (codice). La mesh in `mesh/`, i file di modello `model_*.json` e il progetto QGIS non si toccano. Se un cambiamento li riguarda, si preparano le istruzioni o il frammento di testo da incollare, e lo applica l'utente.

**I layer originali non si modificano.** Ogni risultato si scrive in un file nuovo con suffisso, in questa fase `_50m`. A fine lavoro si controlla con l'impronta SHA-256 che gli originali siano rimasti identici. Se un giorno fosse necessario scrivere su un layer esistente, prima si fa una copia datata (`<layer>_backup_AAAAMMGG.gpkg`) e la si confronta byte per byte. Inoltre l'utente deve chiudere il layer in QGIS mentre viene scritto.

Prima di un'operazione sostanziale si espongono metodo, modifiche previste e domande aperte, e si aspetta la conferma dell'utente. Le cancellazioni e le altre azioni irreversibili richiedono sempre un consenso esplicito.

Tutte le verifiche si eseguono sui file **riletti dal disco** e con codice diverso da quello che li ha prodotti. Così un errore nel codice di produzione non può nascondersi dietro lo stesso errore nel controllo. L'esito si riporta come elenco numerato.

Ogni azione utile al flusso di lavoro si annota in `docs/workflow.md`; le semplici operazioni sui file (rinominare, spostare) no. Gli script stanno in `scripts/`, quelli usati solo per ispezioni e grafici in `scripts/esplorativi/`. Ognuno ha commenti in inglese nel codice e una scheda in italiano in `docs/scripts/`, che spiega come usarlo. L'ordine di esecuzione è in `docs/scripts/README.md`.

## 3. I dati

### 3.1 Il DTM

Il terreno è descritto da `layers/DTM_finale.tif`: celle di 0.25 m, compressione DEFLATE, nodata −9999. Si legge sempre il **valore della cella** che contiene il punto, lo stesso che restituisce lo strumento *Identify* di QGIS. Non si interpola mai: un valore interpolato non esiste nel DTM e non sarebbe ripetibile da chi controlla in QGIS.

### 3.2 I layer

I campi dei layer hanno nomi italiani. `sx` e `dx` indicano la sinistra e la destra orografica, cioè guardando verso valle. Il ciglio è il bordo superiore della sponda, il piede quello inferiore, a contatto con il letto.

| File | Origine | Contenuto |
|---|---|---|
| `breaklines.gpkg` | originale | 1285 linee di discontinuità, con i cigli non ancora allargati. 14 righe hanno geometria vuota o nulla. |
| `boundary.gpkg` | originale | 53 nodestring: condizioni al contorno, ponti P13, P17, P20 e P27, Bordignon, Filippini, edifici di Borgo, divergenza, boale e altre. Nessuna sezione. |
| `regioni_ponti.gpkg` | originale | 176 punti regione. I fid 65 e 135 hanno geometria nulla; i fid 57 e 58 (`muro`) cadono nella stessa faccia. |
| `quote_fisse.gpkg`, `punti_quote_fisse.gpkg`, `quote_fisse_elevation-mesh.2dm` | originali | Non usati in questa fase. |
| `centerline_50m.gpkg` | nuovo | Tre linee d'asse, una per ramo: `N_caldonazzo_borgo`, `V_brenta_vecchio`, `B_borgo_valle`. Il campo `s0_asta` dà la progressiva sull'asta da cui parte B. |
| `centerpoints_50m.gpkg` | nuovo | 735 punti, uno per sezione. `stream` indica il ramo (N, V, B), `s_m` la progressiva reale nel ramo. |
| `bankpoints_50m.gpkg` | nuovo | 1470 punti di sponda, due per sezione. |
| `breaklines_50m.gpkg` | nuovo | Breakline con i cigli allargati e corrette per la regola dei 5 m. |
| `boundary_50m.gpkg` | nuovo | Le 53 nodestring più le 735 sezioni dei tre rami. |
| `regioni_ponti_50m.gpkg` | nuovo | 905 righe, di cui 903 con geometria. |

Prima di riscrivere un file `_50m` se ne fa una copia datata (`_backup_AAAAMMGG`).

I punti regione portano, oltre al nome, il materiale (`mat_id`) e l'area massima degli elementi (`max_area`). Nei dati originali ci sono 29 combinazioni di questi tre valori, e sono queste a definire i materiali del modello.

La tabella completa delle 737 sezioni è in `docs/Brenta_sections_50m_mesh10.csv`.

## 4. Come ragiona BASEmesh

Alcune caratteristiche di BASEmesh condizionano tutto il resto, e conviene averle chiare.

**I nomi delle nodestring devono essere univoci.** Se due stringhe hanno lo stesso nome, BASEmesh tiene l'ultima e scarta l'altra senza avvisare.

**Ogni nodestring deve essere una linea a una sola parte.** Il formato è MultiLineStringZM con Z = M = 0. BASEmesh ordina i nodi di una stringa per distanza dal primo vertice, quindi in una stringa fatta di più pezzi i nodi dei vari pezzi si mescolerebbero. Un nodo che cade entro la tolleranza di due stringhe compare in entrambe.

**Le sezioni si disegnano da sinistra a destra orografica.** In BASEMENT questo corrisponde a `upstream_direction: "right"`.

**Ogni regione chiusa deve contenere esattamente un punto regione.** Le breakline e le nodestring insieme dividono il piano in facce, il cosiddetto grafo planare. BASEmesh assegna a ogni faccia gli attributi del punto che vi cade dentro. Una faccia senza punto resta senza materiale; una con due punti ha attributi ambigui. Ogni volta che si aggiunge o si sposta una linea, quindi, va ricontato il grafo. Lo si ricostruisce con codice proprio prima di scrivere, collegando le estremità che toccano un'altra linea entro 1 mm. Sui layer originali il grafo ha 173 facce.

Dopo ogni modifica alla geometria la mesh va rigenerata in QGIS. Il blocco `STRINGDEF` dei file di modello deve elencare tutte le nodestring, comprese le nuove sezioni.

## 5. La linea d'asse

Le sezioni si posizionano lungo una linea d'asse che segue il centro dell'alveo. La progressiva `s` si misura lungo questa linea, a partire da zero all'inizio di ogni ramo.

La linea d'asse dell'**asta principale** si ricava dallo scheletro di Voronoi del poligono d'alveo. Tra tutti i percorsi dello scheletro da `BC_caldonazzo` a `BC_brenta_valle` si sceglie quello che resta più vicino al centro del letto. Nel poligono d'alveo si conservano i buchi più grandi di 1000 m²: riempirli farebbe collassare i rami. Tra E 677880 e 678420 l'alveo si divide in due. L'asta segue il collegamento nord, più largo (letto mediano 7.4 m contro 4.9 m), e il meandro sud resta senza sezioni.

Il **Brenta vecchio** parte dalla nodestring `divergenza_valle_brenta_vecchio` e arriva alla confluenza, intorno a E 689850. Il percorso è guidato da alcuni punti di passaggio sul letto principale, in modo da non deviare nella striscia parallela del boale né nel collegamento `boale_sifone`.

Lo scheletro è spezzettato, quindi la linea viene lisciata con un filtro gaussiano di ampiezza variabile: 6 m dove il letto è stretto, fino a 60 m dove è largo.

## 6. L'allargamento delle sponde

### 6.1 Perché

Il bankpoint deve stare abbastanza lontano dal ciglio (almeno 5 m) e le sezioni non devono diventare troppo lunghe. Per conciliare le due cose serve che letto e sponde insieme formino un corridoio di larghezza sufficiente. Nei dati originali, nel tratto tra s = 4.2 e 10.2 km, il corridoio misura in mediana solo 31.7 m. Per questo i cigli vanno spostati verso l'esterno.

### 6.2 Il criterio

La larghezza W tra i due cigli si misura ogni metro, perpendicolarmente alla linea d'asse. Si spostano soltanto le linee di ciglio (il confine tra sponda e fascia intermedia); i piedi di sponda restano dove sono.

* **A monte di Borgo e sul Brenta vecchio** il corridoio deve misurare almeno **40.10 m**. Dove W è inferiore, ciascun ciglio si sposta verso l'esterno di metà della differenza, (40.10 − W)/2, in modo simmetrico. I 10 cm in più rispetto ai 40 m servono ad assorbire la semplificazione successiva delle linee.
* **A valle di Borgo** (s > 17 335 m) il fiume si allarga molto: il corridoio misura già da 50 a oltre 200 m, e un minimo fisso di 40 m non avrebbe senso. Qui si chiede invece che **ogni sponda** sia larga almeno **16.05 m**. È la larghezza media di una sponda nel tratto di riferimento, (40.10 − 8.1)/2, dove 8.1 m è la larghezza mediana del letto. Lo spostamento si calcola sponda per sponda.
* Le sponde urbane (`sponda_antro`) e i muri, soprattutto a Borgo, **non si spostano mai**.
* Il ciglio spostato deve restare ad almeno **5 m** dalla linea successiva verso l'esterno, per non creare strisce troppo sottili.

### 6.3 Come si mantiene la topologia

Spostare un ciglio non deve rompere le regioni. Per questo:

* ogni tratto di ciglio conserva il proprio fid e resta collegato ai tratti vicini;
* dove il ciglio finisce sul contorno del dominio o su una linea che non si sposta, la sua estremità scorre lungo quella linea;
* le linee trasversali che terminavano sul ciglio, come le chiusure dei ponti, si prolungano in linea retta fino al nuovo ciglio;
* una nodestring che chiudeva una regione senza una breakline sotto, come `idrometro_Ponte_Zaccon`, si prolunga nella sua stessa direzione (in quel caso di 0.86 e 0.80 m);
* nei punti in cui una linea si innesta su un'altra a T si inserisce un vertice comune, così non nascono facce minuscole.

Le nuove linee si semplificano con una tolleranza di 2 cm, e i vertici più vicini di 2 m si fondono. Gli spostamenti inferiori a un milionesimo di metro si ignorano: sono solo rumore numerico.

Alla fine il grafo planare deve avere **le stesse facce di prima**, senza facce nuove né regioni fuse.

## 7. Le sezioni

Le sezioni sono distanziate di **50 m ± 0.5 m** misurati lungo la linea d'asse. Si controlla anche la distanza in linea retta tra punti d'asse consecutivi, che nelle curve strette può risultare più corta.

Ogni sezione è **perpendicolare alla corda** della linea d'asse tra s − 1 m e s + 1 m. Usare la corda e non la tangente puntuale rende la direzione meno sensibile alle piccole irregolarità della linea. La sezione è un **segmento a due vertici** che va dal bankpoint sinistro al bankpoint destro; i vertici sono copiati esattamente dalle coordinate dei bankpoint.

La posizione si sceglie su tutto il ramo in una volta, non una sezione alla volta. Si generano candidati ogni 0.25 m lungo la linea d'asse e si cerca la sequenza migliore con la programmazione dinamica. Le priorità, in ordine, sono:

1. non incrociare nodestring o linee trasversali esistenti;
2. ridurre le violazioni della regola dei 5 m (§9);
3. tenere il passo il più vicino possibile a 50 m.

La perpendicolarità entra nella scelta come penalità e non come vincolo rigido, altrimenti in alcuni tratti non si troverebbe nessuna sequenza ammissibile. Sul Brenta vecchio anche le sezioni dell'asta principale contano come ostacoli.

Il nome di una sezione è la **lettera del ramo** seguita dalla sua **posizione nel ramo moltiplicata per 50**, a cinque cifre: `N00050` … `N16050`, `V00050` … `V03000`, `B00000` … `B17650`. Il nome è quindi nominale. Su lunghe distanze si discosta dalla posizione vera (alla N16050 la progressiva reale è 16 130 m), che è sempre riportata nel campo `s_m` dei punti d'asse. In `boundary_50m` le sezioni hanno fid da 64 e id da 60, in ordine N, V, B.

**La sezione dell'idrometro di Borgo.** La B00400 coincide esattamente con la nodestring `idrometro_Borgo`: stessi due vertici, con il sinistro per primo. È il punto dove anche nella realtà si misurano le portate, dai livelli, ed è la misura più affidabile di tutto il modello. Per ottenerla tutto il ramo B è stato spostato verso monte di circa 16.6 m rispetto alla disposizione del 17 novembre. Ogni sezione ha come obiettivo la posizione vecchia meno lo spostamento e se ne discosta al massimo di 0.7 m. Il numero di sezioni non cambia. I bankpoint della B00400 sono gli estremi della nodestring, con `tipo` `nodestring`, `regola` `idrometro_Borgo` e la quota della cella. Nessuna sezione cade dentro un ponte: la B00100 è 20 m a valle del Ponte Bordignon e la B17000 9 m a valle del Ponte Filippini.

Una sezione corretta attraversa solo le due linee di piede, e quindi divide soltanto il letto. Fa eccezione la sezione che incontra un muro, come capita a Borgo dove alcuni edifici coincidono con il piede: in quel caso si ferma 0.5 m prima del muro e attraversa una sola linea.

## 8. I bankpoint

Il bankpoint è il punto in cui la sezione finisce su ciascuna sponda. Si cerca il primo rilievo significativo che si incontra salendo dal letto verso l'esterno, non il punto più alto in assoluto: l'intento è avere un punto più vicino al canale rispetto alla cella più alta della sponda.

**Il profilo.** Partendo dal piede di sponda e andando verso l'esterno, si visitano una per una tutte le celle del DTM attraversate dalla sezione e se ne legge il valore. Non si campiona a passo fisso: una cella tagliata solo per un angolo potrebbe sfuggire.

**Il massimo locale.** Un rilievo conta solo se sporge di almeno **5 cm** rispetto al terreno più basso che lo separa da terreno più alto (la sua prominenza). Questo filtra il rumore del DTM. Un tratto piano conta come un unico massimo. Si scartano inoltre i massimi nella **metà inferiore** della sponda, cioè sotto quota z_piede + 0.5·(z_massima − z_piede): sono gobbe al piede, non la sommità.

**La scelta.** Si prende il **primo** massimo valido a partire dal canale. Se non ce n'è nessuno, perché il terreno continua a salire, si prende la **cella più alta** dell'intervallo di ricerca.

**L'intervallo di ricerca.** La ricerca si ferma:

* almeno **5 m prima del ciglio** (allargato), così il bankpoint non finisce sul bordo della sponda;
* a non più di **15 m dalla mezzeria** del corridoio, così i due bankpoint distano al massimo 30 m e la sezione resta compatta.

Dove il letto è più largo di 30 m il piede si trova già oltre i 15 m dalla mezzeria, e il secondo limite non funziona. In quei tratti la ricerca arriva fino a **15 m dal piede di ciascuna sponda**, sempre restando a 5 m dal ciglio. Lo stesso limite si usa quando la mezzeria lascerebbe meno di 2 m di ricerca oltre il piede, come capita alle confluenze.

Infine la ricerca si interrompe **0.5 m prima** di una nodestring, di una linea interna (per esempio un edificio di Borgo) o del piede di un altro letto, a qualunque distanza. Così, dove ci sono due canali affiancati, la sezione non scavalca l'isola. Se l'ostacolo coincide con il piede, come per alcuni edifici di Borgo, la sezione termina 0.5 m prima, dentro il letto.

Se l'utente modifica a mano una sezione, il bankpoint segue il nuovo estremo: `tipo` e `regola` diventano `manuale` e la quota è quella della cella in cui cade. Anche il punto d'asse si aggiorna: è sempre l'intersezione della sezione con la linea d'asse del suo ramo, e da lì si ricalcolano `s_m`, `dist_next` e `dist_cp`. Una sezione può terminare esattamente su un muro o su una nodestring di edificio, come fanno a Borgo alcune sezioni sistemate a mano. I suoi vertici devono comunque avere z = m = 0.

**La posizione.** Il bankpoint si mette a metà del tratto di sezione che attraversa la cella scelta. Se quella cella contiene l'incrocio con il ciglio, il punto va esattamente sull'incrocio.

**Gli attributi.** Ogni punto porta il nome `<sezione>_sx` o `<sezione>_dx`, la progressiva `s_m`, la quota `z_dtm` (il valore della cella) e `dist_cp`, la distanza in pianta dal punto d'asse. Ci sono poi `tipo` (massimo locale o cella più alta), `regola` (quale limite di ricerca è stato applicato) e `prom` (la prominenza).

## 9. La regola dei 5 m

Dove una sezione incrocia una breakline nasce un nodo della mesh. Se a breve distanza c'è un vertice della breakline, tra i due nodi si formano elementi molto piccoli o molto allungati. Per questo **nessun vertice di breakline dovrebbe trovarsi tra 0 e 5 m da un incrocio** con una sezione.

Il vertice dell'altro piede della stessa sezione non conta: in un letto largo meno di 5 m cade per forza entro 5 m, ed è un nodo della sezione, non della breakline.

**Come si corregge.** Si sposta sempre la breakline, mai la nodestring, e il punto d'incrocio resta esattamente dov'è:

1. ogni incrocio di una sezione o di una nodestring con una breakline diventa un vertice fisso della breakline. Lo stesso vale per ogni innesto a T, cioè una linea che termina sul tratto interno di un'altra: così togliere un vertice non può mai staccare una linea e fondere due regioni;
2. i vertici intermedi entro 5 m dall'incrocio si tolgono;
3. un nodo condiviso con altre linee si porta sull'incrocio, e le linee collegate lo seguono;
4. un nodo che appartiene a un'altra linea (per esempio sul piede opposto) si fa scorrere lungo la sua linea fino a 5.05 m dall'incrocio;
5. se una breakline trasversale (per esempio il limite di una sorgente) passa a pochi metri da una sezione, si porta sulla sezione. I suoi estremi scorrono lungo i piedi, e la striscia sottile tra le due linee sparisce.

Ogni operazione si accetta solo se:

* la rete di linee non si sposta di più di **2 m**;
* non nascono incroci tra linee;
* non si toccano vertici che stanno su una nodestring;
* nessun punto regione si trova più vicino di 1 m a una linea, o più vicino di prima se lo era già.

Le breakline che delimitano le regioni di muro (`mat_id` 11), compresi i tratti di piede su cui i muri poggiano, **non si toccano mai**: restano identiche all'originale.

I casi che non rispettano questi limiti restano violazioni e si segnalano. Alcune sono accettate come eccezioni: l'elenco completo è al §14 bis. Dopo lo spostamento del ramo B del 18 novembre la B13100 non ha più violazioni e non è più un'eccezione. Si cerca comunque di ridurle già nella scelta della posizione delle sezioni (§7), penalizzando anche i piedi a meno di 5 m da un incrocio tra nodestring e breakline.

## 10. I punti regione

Le nuove sezioni dividono il letto in nuove facce, e ognuna deve ricevere il suo punto regione. Le regole sono:

* in ogni faccia del grafo finale c'è **un solo punto**;
* se due regioni si fondono, si tiene il punto originale, se c'è, altrimenti quello con il fid più basso;
* il punto tenuto deve stare **ad almeno 1 m** da ogni linea, altrimenti si sceglie un altro candidato;
* un punto originale non si sostituisce mai, nemmeno nelle strisce strette (muri larghi meno di 2 m) dove nessun punto può stare a 1 m dalle linee;
* i punti esistenti che si tengono non si spostano e non cambiano attributi;
* una faccia nuova riceve un punto nel luogo più lontano dai suoi bordi, con gli attributi della regione d'alveo da cui deriva;
* un punto esistente che finisce a meno di 1 m da una nuova sezione viene sostituito da un punto nuovo nella stessa regione (è successo al fid 41);
* i difetti già presenti nei dati originali, cioè i punti con geometria nulla e la faccia con due punti, restano come sono.

## 11. Scrittura dei file e ambiente

I GeoPackage si scrivono con GDAL/OGR, mantenendo tipo di geometria, sistema di riferimento, campi e indice spaziale dell'originale. Se GDAL non fosse disponibile, si può scrivere con SQLite in un'unica transazione. In quel caso vanno aggiornati a mano l'intestazione binaria e l'envelope di ogni geometria, l'indice R-tree, l'estensione in `gpkg_contents` e il conteggio in `gpkg_ogr_contents`.

Sul computer ci sono due ambienti Python:

* quello di Anaconda (`python3`), con geopandas, shapely 2.1, numpy, scipy e networkx;
* quello di sistema (`/usr/bin/python3`), con GDAL/OGR e PyQGIS ma senza shapely.

Per questo gli script che leggono il DTM o scrivono i GeoPackage usano il secondo.

## 12. Le verifiche

Dopo ogni modifica, sui file riletti dal disco, si controlla che:

1. il numero di feature sia quello atteso;
2. nomi e id siano univoci;
3. tipo di geometria, sistema di riferimento e campi non siano cambiati;
4. `PRAGMA integrity_check` dia ok, e l'indice R-tree contenga tante voci quante sono le geometrie non nulle;
5. le feature non toccate siano identiche all'originale;
6. il passo tra le sezioni rispetti i 50 ± 0.5 m lungo la linea d'asse, e la distanza in linea retta sia controllata;
7. le sezioni siano perpendicolari, a due vertici, con il primo a sinistra e coincidenti con i bankpoint;
8. nessuna sezione ne incroci un'altra o una nodestring, tranne la B00400, che coincide con `idrometro_Borgo`;
9. ogni sezione attraversi le linee previste;
10. ogni faccia abbia un solo punto, senza conflitti di attributi;
11. `z_dtm` sia uguale al valore della cella, e ogni bankpoint stia ad almeno 5 m dal ciglio;
12. i bankpoint, ricalcolati con codice indipendente, coincidano;
13. dopo l'allargamento la larghezza, campionata ogni 0.5 m, rispetti il criterio;
14. siano contate le violazioni della regola dei 5 m;
15. l'impronta SHA-256 dei layer originali sia invariata.
16. dopo ogni modifica a mano, tutti gli attributi di linee d'asse, punti d'asse, bankpoint e punti regione siano coerenti con le geometrie (`verify3.py`), e le quote dei bankpoint coincidano con il DTM (`verify3_dtm.py`).

## 13. Difetti noti nei dati originali

Sono già presenti nei dati di partenza e si lasciano come sono:

* in `breaklines.gpkg`, 14 righe hanno geometria vuota o nulla;
* in `regioni_ponti.gpkg`, i fid 65 e 135 hanno geometria nulla, e i fid 57 e 58 cadono nella stessa faccia.

## 14. Cosa resta da fare (al 18 novembre 2026, pomeriggio)

1. **Passo lungo la linea d'asse oltre 50.5 m di pochi millimetri:** N01950–N02000 (50.505 m), B00150–B00200 (50.504 m) e B00450–B00500 (50.505 m). Dipendono dalle sezioni modificate a mano, il cui punto d'asse si è spostato di qualche millimetro.
2. **Mesh e modello.** La mesh va rigenerata da `breaklines_50m`, `boundary_50m` e `regioni_ponti_50m`, e `STRINGDEF` va aggiornato con le 735 sezioni dai nuovi nomi. La B00400 e `idrometro_Borgo` sono coincidenti; va verificato come le trattano BASEmesh e BASEMENT.
3. **Controllo della mesh.** Dopo la generazione va verificata la qualità degli elementi vicino ai bankpoint, alle violazioni dei 5 m, ai cigli allargati e alle strisce di muro, e che i materiali corrispondano alle regioni.

Su indicazione dell'utente non si seguono più questi punti:
* l'allargamento incompleto sul Brenta vecchio urbano;
* i due bankpoint non confermati dal ricalcolo indipendente (ex S09338 sx e S30831 dx).

## 14 bis. Eccezioni

Le eccezioni accettate dall'utente sono divise in due categorie. L'elenco comprende tutte e sole queste sezioni.

**Regola dei 5 m**

| Sezioni | Motivo |
|---|---|
| N16000 | I suoi incroci con i piedi stanno a 3.13 e 3.06 m da quelli della nodestring `check_portata_Brenta_nuovo`, che non si sposta. |
| B00000, B00100, B00150, B00200, B00300, B00400, B00450, B00500 | Zona dei muri di Borgo: il vertice entro 5 m appartiene a una linea dei muri (`mat_id` 11), che è bloccata. Le distanze sono 1.47; 2.34 e 1.05; 2.47; 2.18; 3.21, 0.87 e 0.87; 3.57; 2.89; 1.42 m (accettate il 18 novembre). |

**Passo tra sezioni consecutive** (50 ± 0.5 m)

| Sezioni | Motivo |
|---|---|
| N01900–N01950 | Curva stretta: 50.5 m lungo la linea d'asse, 46.68 m in linea retta. |
| B11200–B11250 | Curva stretta attorno alla progressiva 27 470 m dell'asta: 50.5 m lungo la linea d'asse, 47.85 m in linea retta. |
| B00250–B00300–B00350 | B00300 spostata a mano dall'utente nella zona dei muri di Borgo: 47.14 e 53.61 m lungo la linea d'asse, 47.03 e 53.16 m in linea retta. |

## 15. Come si è arrivati a questo metodo

| Data | Passo | Stato |
|---|---|---|
| 28 ottobre 2026 | Sezioni ogni 200 m estese a tutta la valle | superato |
| 2 novembre 2026 | Sezioni divise in parte d'alveo e parti laterali | superato |
| 5 novembre 2026 | Bankpoint, sezioni a due vertici, corridoio di 40 m, regola dei 5 m | valido |
| 9 novembre 2026 | Sezioni ogni 50 m su un tratto di prova di 6 km | valido |
| 9 novembre 2026 | Metodo esteso ai 34 km dell'asta e al Brenta vecchio | valido |
| 17 novembre 2026 | Tre rami N, V, B con nomi nominali; correzione della regola dei 5 m sulle breakline | valido |
| 18 novembre 2026 | Ramo B spostato di 16.6 m verso monte, B00400 coincidente con `idrometro_Borgo` | stato attuale, vedi `workflow.md` |
