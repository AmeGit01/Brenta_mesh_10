# Registro del lavoro

Questo registro racconta in ordine cronologico cosa è stato fatto sui dati del Brenta, con le decisioni prese, i numeri ottenuti e le verifiche eseguite. Le regole generali e il perché delle scelte sono spiegati in [Brenta_regole_e_metodo.md](Brenta_regole_e_metodo.md). Gli script usati sono in `scripts/` e sono descritti in [scripts/README.md](scripts/README.md).

La richiesta di partenza era replicare il lavoro descritto nei documenti di `docs/` con sezioni ogni 50 m ± 0.5 m, usando i dati di `layers/`.

## 9 novembre 2026

### Lettura dei documenti e inventario dei dati

Ho letto i quattro documenti di partenza: le note di passaggio di consegne, il report sulla suddivisione delle nodestring, quello sui bankpoint e quello sulle sezioni a 50 m. Questi documenti sono stati poi riassunti in `Brenta_regole_e_metodo.md` ed eliminati.

Poi ho fatto l'inventario di `layers/`, leggendo solo metadati e attributi. La prima sorpresa è stata che **i dati non corrispondevano a quelli descritti nei report**. I report parlavano di un tratto di prova di circa 6 km, mentre in `layers/` c'era l'intero modello:

| | Nei report (tratto di prova) | In `layers/` |
|---|---|---|
| Estensione | circa 6 km, E 679780–684663 | circa 30 km, E 675836–705405 |
| `boundary.gpkg` | 34 feature, comprese le sezioni `S****` | 53 feature (condizioni al contorno, ponti P13, P17, P20, P27, Bordignon, Filippini, edifici di Borgo, divergenza, boale…) e nessuna sezione |
| `regioni_ponti.gpkg` | 44 punti | 176 punti, con 29 combinazioni di nome, materiale e area massima |
| `breaklines.gpkg` | cigli già allargati a 40 m | 1285 feature, stato da verificare |
| Linea d'asse, punti d'asse, bankpoint | presenti | assenti |
| DTM | ritaglio `DTM_finale_clip.tif` | solo il DTM completo `DTM_finale.tif` (0.25 m, nodata −9999) |

In più c'erano `quote_fisse.gpkg`, `punti_quote_fisse.gpkg` e `quote_fisse_elevation-mesh.2dm`, che non riguardano questa fase. Sul computer erano disponibili GDAL da riga di comando, il Python di sistema con GDAL e PyQGIS e il Python di Anaconda con geopandas, shapely 2.1.2 e numpy.

### Analisi del dominio

Per non interferire con QGIS ho lavorato su copie di `boundary`, `breaklines` e `regioni_ponti` in una cartella temporanea.

Il grafo planare formato da breakline e nodestring ha **173 facce**. Nessuna è senza punto regione, ma una ne contiene due (fid 57 e 58), e due punti (fid 65 e 135) non cadono in nessuna faccia perché hanno geometria nulla. In `breaklines` ci sono 14 righe con geometria vuota o nulla.

Dallo scheletro del poligono d'alveo ho misurato un'asta principale di circa 34.1 km, da `BC_caldonazzo` a `BC_brenta_valle`, pari a circa 682 sezioni a 50 m. A questa si aggiungono 17 rami laterali, per 9.1 km in tutto. Lungo l'asta la larghezza del corridoio (letto più sponde) cambia molto:

| Tratto | Progressiva (km) | Corridoio: 5° perc. / mediana / 95° perc. (m) | Letto, mediana (m) | Quota sotto 40 m |
|---|---|---|---|---|
| Caldonazzo – P13 | 0 – 3.9 | 25.9 / 30.6 / 52.5 | 5.2 | 78 % |
| Tratto di prova dei report | 4.2 – 10.2 | 28.2 / 31.7 / 39.2 | 8.1 | 99 % |
| P20 – divergenza | 10.2 – 13.2 | 33.8 / 40.1 / 42.1 | 9.1 | 48 % |
| Borgo (divergenza – confluenza) | 13.2 – 17.3 | 49.8 / 58.4 / 70.8 | 9.4 | 2 % |
| A valle di Borgo | 17.3 – 22.8 | 50.2 / 66.5 / 141.1 | 15.6 | 0 % |
| Valle | 22.8 – 34.1 | 77.9 / 100.4 / 219.4 | 29.3 | 0 % |

Da questi numeri ho tratto quattro conclusioni.

* I dati di `layers/` sono quelli **precedenti all'allargamento** dei cigli. Nel tratto di prova la mediana è 31.7 m, lo stesso valore che i report indicavano prima di allargare.
* Il limite di ricerca dei bankpoint a 15 m dalla mezzeria funziona solo con un corridoio di circa 40 m. Dove il letto supera i 30 m, circa 6.4 km dell'asta, il piede è già oltre i 15 m e la regola non si può applicare così com'è.
* Il corridoio è più stretto di 40 m su circa 10.8 km, quasi tutti a monte di Borgo.
* Serviva una linea d'asse nuova, perché `layers/` non ne conteneva una.

A questo punto non avevo ancora scritto né modificato nulla, e ho chiesto all'utente come procedere.

### Decisioni dell'utente

* Le sezioni si fanno sull'**asta principale e sul Brenta vecchio**.
* L'allargamento dei cigli va scritto in un **file nuovo**, senza toccare `breaklines.gpkg`. Dopo Borgo il fiume si allarga molto, quindi il criterio dei 40 m va adattato.
* Dove il letto supera i 30 m, la ricerca del bankpoint arriva fino a **15 m dal piede di ciascuna sponda**, sempre restando a 5 m dal ciglio.

### Linee d'asse

La linea d'asse dell'**asta principale** segue lo scheletro del poligono d'alveo da `BC_caldonazzo` a `BC_brenta_valle`, preferendo il centro del letto. Dopo la lisciatura è lunga 33 981.6 m.

Il **Brenta vecchio** va dalla `divergenza_valle_brenta_vecchio` alla confluenza, intorno a E 689850, ed è lungo 3 058.7 m. Per tenerlo sul letto principale ho imposto alcuni punti di passaggio; senza, il percorso deviava nella striscia parallela del boale o nel collegamento `boale_sifone`.

La lisciatura usa un filtro gaussiano di ampiezza 6 m dove il letto è stretto, fino a 60 m dove è largo.

Tra E 677880 e 678420 l'alveo si divide in due rami. Ho fatto passare l'asta per il collegamento nord, più largo (letto mediano 7.4 m), e non per il meandro sud (4.9 m), che resta quindi senza sezioni. È una mia scelta, da confermare.

### Allargamento dei cigli

Il criterio adottato riprende quello dei report e lo adatta a valle di Borgo:

* **a monte di Borgo e sul Brenta vecchio** il corridoio deve misurare almeno 40.10 m, e ogni ciglio si sposta di (40.10 − W)/2;
* **a valle di Borgo** (s > 17 335 m) il corridoio è già di 50–220 m, quindi un minimo di 40 m non ha senso. Lì ogni sponda deve essere larga almeno **16.05 m**, che è la larghezza media di una sponda nel tratto di prova ((40.10 − 8.1)/2). Lo spostamento si calcola sponda per sponda;
* le sponde urbane e i muri di Borgo non si spostano;
* il ciglio resta sempre ad almeno 5 m dalla linea successiva verso l'esterno.

Per non rompere le regioni ho dovuto sistemare alcune linee collegate ai cigli:

* le chiusure dei ponti P13, P17 e P20 (fid 1113–1116, 1421 e 1422) sono state prolungate in linea retta fino ai nuovi cigli;
* le estremità dei cigli fid 17, 1001 e 1061 scorrono sul contorno o sulle linee che non si spostano;
* la nodestring `idrometro_Ponte_Zaccon` è stata prolungata nella sua direzione di 0.86 e 0.80 m. Senza prolungamento, la regione di sponda non sarebbe più rimasta chiusa.

Dopo lo spostamento il grafo ha ancora **173 facce**, come all'origine, senza facce nuove né regioni fuse. Resta solo la faccia con due punti già presente nei dati originali (fid 57 e 58, `muro`).

### Sezioni, bankpoint e regioni

**Posizione.** Per ogni ramo ho generato candidati ogni 0.25 m lungo la linea d'asse e ho scelto la sequenza migliore su tutto il ramo, con passo tra 49.5 e 50.5 m. Le priorità, in ordine:

1. non incrociare nodestring e linee trasversali;
2. ridurre le violazioni della regola dei 5 m;
3. restare vicino a 50 m.

Sul Brenta vecchio anche le sezioni dell'asta contano come ostacoli. Ogni sezione è perpendicolare alla corda della linea d'asse tra s − 1 m e s + 1 m e parte dalla sponda sinistra.

**Bankpoint.** Ho applicato la regola dei report: primo massimo locale con prominenza di almeno 5 cm, ignorando la metà inferiore della sponda, oppure, in mancanza, la cella più alta. Ogni cella attraversata dal profilo viene letta, senza interpolazione. La ricerca resta ad almeno 5 m dal ciglio e a non più di 15 m dalla mezzeria. Dove il letto supera i 30 m vale il limite di 15 m dal piede deciso dall'utente. L'ho usato anche dove la mezzeria, spostata per esempio alle confluenze, lasciava meno di 2 m di ricerca. Questa estensione è una mia scelta.

Ho aggiunto due limiti alla ricerca. Il bankpoint si ferma 0.5 m prima di una nodestring o di una linea interna, come gli edifici di Borgo. Si ferma anche 0.5 m prima del letto di un altro ramo vicino: è successo su 22 lati, soprattutto sul Brenta vecchio.

In quattro casi a Borgo un edificio coincide con il piede della sponda: S16382 dx, S16432 dx, S16533 sx e S16583 dx. Lì la sezione si ferma 0.5 m prima del muro, dentro il letto, e non attraversa il piede.

**Nomi.** Le sezioni prendono il nome dalla progressiva reale, a cinque cifre: `S00050` … `S33940` sull'asta e `V00050` … `V03058` sul Brenta vecchio. Una numerazione nominale come quella dei report, su questa lunghezza, si sarebbe scostata fino a 140 m dalla posizione vera. Le sezioni hanno fid da 64 a 800 e id da 60 a 796.

**Regioni.** Il grafo finale ha 905 facce. Ho aggiunto **733 punti** nelle nuove facce del letto, con gli attributi della regione d'alveo da cui derivano. Il punto originale fid 41 (`source_3_brenta_3`) cadeva a 0.04 m da una nuova sezione ed è stato sostituito da uno nuovo nella stessa regione; tutti gli altri punti originali sono rimasti. I fid 65 e 135, senza geometria fin dall'origine, sono rimasti così.

**File scritti.** Tutti in `layers/`, senza modificare gli originali: l'impronta SHA-256 di `boundary`, `breaklines` e `regioni_ponti` è rimasta identica.

| File | Contenuto |
|---|---|
| `centerline_50m.gpkg` | Le due linee d'asse: `asta_principale` (33 981.6 m) e `brenta_vecchio` (3 058.7 m) |
| `centerpoints_50m.gpkg` | 737 punti d'asse, con i campi `nome`, `stream`, `s_m`, `dist_next` |
| `bankpoints_50m.gpkg` | 1474 bankpoint, con i campi `nome`, `sezione`, `s_m`, `z_dtm`, `dist_cp`, `tipo`, `regola`, `prom` |
| `breaklines_50m.gpkg` | Copia di `breaklines` con 272 feature modificate: cigli allargati e linee collegate |
| `boundary_50m.gpkg` | Le 53 nodestring originali (52 identiche, `idrometro_Ponte_Zaccon` prolungata) più le 737 sezioni |
| `regioni_ponti_50m.gpkg` | 908 righe, di cui 906 con geometria |

La tabella delle 737 sezioni, con quote, tipo, regola, prominenza e lunghezza, è in `docs/Brenta_sections_50m_mesh10.csv`.

### Verifiche

Ho eseguito tutte le verifiche sui file riletti dal disco, con codice separato da quello di produzione.

1. **Conteggi corretti:** `breaklines_50m` 1285, `boundary_50m` 790 (53 + 737), `regioni_ponti_50m` 908, `centerpoints_50m` 737, `bankpoints_50m` 1474.
2. **Nomi e id** delle sezioni tutti univoci.
3. **Struttura dei file:** tipo di geometria e sistema di riferimento invariati, `integrity_check` ok, indice spaziale completo.
4. **Feature non toccate:** identiche all'originale (999 breakline, 52 nodestring, 173 punti regione).
5. **Passo lungo la linea d'asse:** sempre in tolleranza, tra 49.75 e 50.50 m sull'asta e tra 49.50 e 50.50 m sul Brenta vecchio.
6. **Distanza in linea retta tra punti d'asse:** in quattro casi scende sotto i 49.5 m, tutti in curve strette o in punti dove la linea fa una punta. Le coppie partono da s = 1914 (46.68 m), 16180 (48.05 m) e 16231 (49.31 m) sull'asta, e da s = 3008 (48.73 m) sul Brenta vecchio.
7. **Geometria delle sezioni:** perpendicolari alla corda (scarto massimo 6.5·10⁻⁹ gradi), con due vertici, il primo a sinistra, coincidenti con i bankpoint.
8. **Incroci:** nessuna sezione ne incrocia un'altra o una nodestring.
9. **Linee di piede:** 733 sezioni attraversano esattamente le due linee di piede; le quattro contro i muri ne attraversano una.
10. **Punti regione:** il grafo finale ha 905 facce, ognuna con un punto, più la faccia con due punti già presente all'origine.
11. **Quote e distanza dal ciglio:** la quota di tutti i 1474 bankpoint coincide con il valore della cella, e tutti stanno ad almeno 5 m dal ciglio.
12. **Ricalcolo indipendente dei bankpoint** con campionamento a 1 cm: coincidono 1446 punti su 1474. Delle 28 differenze, 26 sono celle attraversate per meno di 1 cm, che il campionamento non vede. Gli altri due casi (S09338 sx e S30831 dx) hanno con buona probabilità la stessa causa, ma non l'ho dimostrato.
13. **Larghezza dopo l'allargamento**, campionata ogni 0.5 m:
    * sull'asta a monte di Borgo il corridoio è sotto i 40 m solo nello 0.17 % dei campioni (59 su 34 669), in punti isolati e all'inizio dell'asta (minimo 34.4 m a s = 1–2 m);
    * a valle di Borgo una sponda è sotto i 16 m solo in punti isolati e negli ultimi metri, tra s = 33 957 e 33 980, dove il corridoio arriva all'uscita e non ci sono sezioni;
    * sul Brenta vecchio il corridoio è sotto i 40 m in 397 campioni su 6112, soprattutto tra s = 2731 e 2910, dove le sponde urbane non si spostano (minimo 31 m), e tra s = 1090 e 1104;
    * i cigli spostati non si intersecano mai con sé stessi. Le 11 linee che risultano incrociare altre linee sono i tagli dei ponti sui piedi di sponda, già presenti nei dati originali (10 coppie), più un caso in cui una linea tocca un vertice.

### Questioni aperte

* **Regola dei 5 m.** In 266 incroci su 1470, distribuiti su 182 sezioni, c'è un vertice di breakline a meno di 5 m. In 40 casi la distanza è sotto 0.5 m, con un minimo di 0.018 m nella sezione S12654: lì è probabile che nascano elementi molto piccoli. Come previsto dalle regole, le linee di piede non sono state toccate.
* **Punti regione vicini alle linee.** Tre nuovi punti stanno a meno di 1 m da una linea, perché le loro regioni sono troppo strette: fid 485 (0.14 m), 504 (0.19 m) e 568 (0.69 m).
* **Confronto con i report.** Non è stato possibile confrontare il metodo con i 60 bankpoint dei report, perché in `layers/` mancano le sezioni e la linea d'asse di allora.
* **Mesh.** La mesh non è ancora stata rigenerata. Va costruita in QGIS/BASEmesh da `breaklines_50m`, `boundary_50m` e `regioni_ponti_50m`, e il blocco `STRINGDEF` va aggiornato con le 737 nuove sezioni.

## 17 novembre 2026

### Punto di partenza

Le richieste dell'utente erano quattro:

* sistemare tutti gli incroci secondo la regola dei 5 m, spostando sempre le breakline e mai le nodestring, e senza spostare i punti d'incrocio;
* risolvere i punti regione troppo vicini alle linee;
* separare i tre rami alla confluenza di Borgo, che un modello 1D non può riprodurre;
* rinominare tutte le sezioni.

Le altre due questioni aperte (passo in linea retta e confronto con i report) sono state lasciate da parte su sua indicazione.

Prima di tutto ho confrontato i file `_50m` con quelli scritti il 9 novembre, per capire cosa avesse già corretto l'utente a mano:

* 21 breakline semplificate nel tratto a monte (E < 679 100), 6 delle quali svuotate, e la breakline 1101 eliminata vicino alla `check_portata_Brenta_nuovo`;
* la nodestring `check_portata_Brenta_nuovo` allungata fino a comprendere anche il canale di destra;
* le sezioni S00151 e S01965 allungate sul lato sinistro, sulla stessa retta, di 2.42 e 1.22 m. In origine i loro estremi sfioravano una breakline a pochi centimetri;
* il punto regione 504 spostato di 4.3 m.

Tutte queste modifiche sono state mantenute. Sullo stato di partenza restavano 264 incroci in violazione della regola dei 5 m.

### Decisioni dell'utente

* **Rami.** I rami diventano tre, ciascuno con la sua lettera: N da Caldonazzo a Borgo, V per il Brenta vecchio, B da Borgo in poi. I rami restano collegati nella mesh 2D; sono le sezioni a fare da estremi dei rami, mentre le condizioni al contorno del modello 1D le imposta l'utente.
* **Nomi.** Il numero di ogni sezione è la sua posizione nel ramo moltiplicata per 50, indipendentemente dalla progressiva reale, che resta nel campo `s_m` di `centerpoints_50m`. Il ramo B parte da B00000.
* **Progressiva.** La progressiva di B parte da zero in B00000; N e V mantengono quella di prima.
* **Ponte Bordignon.** La B00050 deve stare almeno 5 m a monte del ponte.
* **Regola dei 5 m.** Si accetta che una linea si sposti al massimo di 2 m per singola correzione.

### Nuova suddivisione delle sezioni

* **Ramo N:** le prime 321 sezioni dell'asta, fino all'ex S16130, che diventa **N16050**. Geometrie invariate, comprese le due allungate dall'utente. La N16050 è stata allungata verso destra fino a comprendere il canale parallelo (`bed_borgo`). Il nuovo bankpoint destro è stato cercato con la stessa regola, dal piede del canale di destra verso l'esterno, fermandosi 0.5 m prima della striscia di muro. Non c'è un massimo locale, quindi vale la cella più alta, a 0.84 m dal muro (z = 384.79 m). La sezione ora misura 27.3 m e attraversa i due canali e l'isola che li separa.
* **Ramo V:** le prime 60 sezioni del Brenta vecchio, fino all'ex V03008, che diventa **V03000**. Geometrie invariate.
* **Eliminate:** S16180, S16231, la vecchia S16282 e tutte le sezioni a valle, oltre alla V03058.
* **Ramo B:** 354 sezioni nuove, da **B00000** (s = 16 269.75 m sull'asta, 11.75 m più a monte della vecchia S16282) a **B17650**. La B00050 cade a s = 16 319.75 m, 8.2 m prima del ponte e a 5.0 m dai suoi incroci con i piedi di sponda. Le posizioni sono state ottimizzate con lo stesso metodo del 9 novembre (candidati ogni 0.25 m, passo 49.5–50.5 m), aggiungendo una penalità per i piedi a meno di 5 m da un incrocio tra nodestring e breakline. Una soluzione con B00000 32 m più a monte costava meno, ma è stata scartata perché spostava l'inizio del ramo più di quanto chiesto.
* **Riproducibilità.** I bankpoint del ramo B sono stati calcolati con la stessa catena di script. Rilanciata su otto sezioni esistenti, la riproduce esattamente, salvo due lati spostati di 5 e 12 cm (S16382 sx e S16432 sx). Lì la nuova versione applica alla lettera il margine di 0.5 m dagli ostacoli.
* **Limite di ricerca ricostruito.** Il passo che fermava la ricerca 0.5 m prima di nodestring e linee interne non era mai stato salvato come script: l'ho ricostruito. Adesso ferma la ricerca anche prima del piede di un altro letto a qualsiasi distanza. Prima lo faceva solo entro 17 m, e nei tratti a due canali la sezione B01600 attraversava l'isola fino al secondo letto.
* **Sezioni contro gli edifici di Borgo.** B00100, B00150 e B00250 terminano su un lato 0.5 m prima di un edificio. B00200 ha gli edifici su entrambi i lati, quindi non attraversa nessuna breakline.

### Regola dei 5 m

Gli incroci non si spostano mai: ogni punto in cui una sezione o una nodestring incrocia una breakline è stato inserito come vertice fisso della breakline. Prima ancora ho reso espliciti gli 87 innesti a T, cioè le linee che terminavano sul tratto interno di un'altra linea senza un vertice in comune. Senza questo passo, togliere un vertice poteva staccarle e fondere due regioni, come è successo in una prima prova.

Poi, per ogni incrocio:

* i vertici intermedi entro 5 m sono stati tolti;
* i nodi condivisi con altre linee sono stati portati sull'incrocio insieme alle linee collegate;
* quando un nodo stava sul piede opposto, l'ho fatto scorrere lungo la sua linea fino a 5 m.

Ogni singola operazione è stata accettata solo se:

* non deformava la rete di linee di più di 2 m;
* non creava nuovi incroci tra linee;
* non toccava vertici che stanno su una nodestring;
* non avvicinava una linea a un punto regione sotto 1 m, o sotto la sua distanza di prima se era già minore.

Una prima versione senza quest'ultimo controllo portava una linea a 6 cm dal punto originale 57.

Nei letti larghi meno di 5 m l'incrocio con il piede opposto della stessa sezione cade entro 5 m. Quello è un nodo della sezione stessa e non viene contato come violazione.

Due casi sono stati risolti come chiesto per il punto 485:

* **Punto 485:** la breakline 1225, che separa il letto dalla sorgente `source_brenta_nuovo`, è stata portata esattamente sulla N15050 (ex S15120). I suoi estremi scorrono di 0.29 e 0.17 m lungo i piedi. La striscia sottile che conteneva il punto 485 non esiste più.
* **Sorgente `source_3_brenta_3`:** la N11750 (ex S11804) attraversava la striscia di sorgente, larga circa 7 m, delimitata dalle linee 987 e 988. La 987 è stata portata sulla sezione e la 988 fatta scorrere lungo i piedi fino a 5.05 m dagli incroci. La striscia ora è larga circa 5 m.

Sono state modificate 547 breakline: 238 vertici rimossi, 58 nodi portati sugli incroci, 4 nodi fatti scorrere. Restano **9 violazioni** su 1469 incroci, che non si possono risolvere senza spostare nodestring o deformare le linee oltre il limite:

* N16000, a 3.13 e 3.06 m: sono gli incroci della `check_portata_Brenta_nuovo` con i piedi;
* B00000 (4.30 m), B00100 (1.40 m), B00350 (3.38 m) e B00450 (4.22, 4.60 e 4.60 m), tra i muri, le paratoie e gli edifici di Borgo. Per la B00100 la correzione è stata rifiutata perché avrebbe portato una linea a 6 cm dal punto originale 57;
* B13100 (4.37 m).

### Punti regione

Il grafo finale ha **902 facce**, ognuna con un punto, più la coppia 57/58 già presente nei dati originali.

* **Punti tolti:** 31. Tra questi il 485, la cui striscia è sparita, e il 568, rimasto nella faccia del Ponte Bordignon ora che non c'è più una sezione sul ponte. Gli altri 29 sono punti creati il 9 novembre, rimasti doppioni o troppo vicini a una sezione dopo il riposizionamento del ramo B.
* **Punti nuovi:** 28, con gli attributi della regione originale da cui deriva la faccia: 24 `bed`, 3 `bed_borgo` e 1 `sponda_antro`. Quest'ultimo serve all'isola tagliata dalla N16050.
* **Punti originali:** tutti presenti e non spostati, anche quelli nelle strisce di muro larghe meno di 2 m, dove nessun punto può stare a 1 m dalle linee.
* **Punto 504:** quello spostato dall'utente resta, a 1.26 m dalle linee.

### File scritti

Prima di scrivere ho fatto una copia datata (`*_backup_20261117.gpkg`) di ognuno dei sei file `_50m`, verificata con SHA-256. L'utente aveva chiuso i layer in QGIS. Gli originali `breaklines`, `boundary` e `regioni_ponti` non sono stati toccati.

| File | Contenuto |
|---|---|
| `breaklines_50m.gpkg` | 547 linee modificate per la regola dei 5 m e per i punti 485 e `source_3_brenta_3` |
| `boundary_50m.gpkg` | Le 53 nodestring, identiche a prima, più le 735 sezioni N, V e B; 788 feature |
| `regioni_ponti_50m.gpkg` | 905 righe, di cui 903 con geometria |
| `centerline_50m.gpkg` | Tre linee: `N_caldonazzo_borgo` (16 130.0 m), `V_brenta_vecchio` (3 008.3 m), `B_borgo_valle` (17 711.2 m). Nuovi campi `ramo` e `s0_asta`, la progressiva sull'asta da cui parte B |
| `centerpoints_50m.gpkg` | 735 punti; `stream` vale N, V o B; `s_m` è la progressiva nel ramo |
| `bankpoints_50m.gpkg` | 1470 punti. I due lati allungati dall'utente hanno `tipo` e `regola` = `manuale` e la quota della cella DTM nella nuova posizione |

Ho rigenerato anche la tabella `docs/Brenta_sections_50m_mesh10.csv` dai file nuovi. Ha 735 righe e una colonna in più, `ramo`.

Gli script usati sono in `scripts/`, descritti in `docs/scripts/README.md`.

### Verifiche (sui file riletti dal disco, con codice separato)

1. **Conteggi:** breakline 1284, boundary 788 (53 + 735), regioni 905, punti d'asse 735, bankpoint 1470, linee d'asse 3.
2. **Nomi:** N00050–N16050 (321), V00050–V03000 (60), B00000–B17650 (354). Multipli di 50 consecutivi, tutti univoci.
3. **Nodestring:** le 53 non di sezione sono identiche a prima, comprese le modifiche dell'utente.
4. **Sezioni e bankpoint:** ogni sezione ha due vertici, identici ai suoi bankpoint, da sinistra a destra.
5. **Passo:** lungo la linea d'asse sempre tra 49.75 e 50.50 m. In linea retta l'unica eccezione è quella già nota, N01900 (46.68 m).
6. **Ponte Bordignon:** la B00050 sta 8.22 m a monte del ponte lungo la linea d'asse, e a 7.83 m nel punto più vicino.
7. **Incroci tra sezioni:** nessuna sezione ne incrocia un'altra o una nodestring.
8. **Regola dei 5 m:** 9 violazioni su 1469 incroci, quelle elencate sopra.
9. **Incroci fermi:** tutti gli incroci delle sezioni stanno sulle breakline di prima, salvo la 987 e la 1225, che ora coincidono con le sezioni N11750 e N15050. Anche gli incroci tra nodestring e breakline sono rimasti al loro posto.
10. **Breakline:** 717 identiche a prima, 547 modificate. Il campo `id` è invariato.
11. **Grafo finale:** 902 facce, nessuna senza punto. L'unica con due punti è quella preesistente (57/58).
12. **Punti regione originali:** tutti presenti e non spostati.
13. **Struttura dei file:** `integrity_check` ok, sistema di riferimento 25832. Nei sei file l'indice spaziale conta tante voci quante geometrie, tranne `breaklines_50m`: lì 6 geometrie vuote (fid 447, 902, 917, 967, 1209, 1223) non sono indicizzate, esattamente come nel backup.
14. **Originali:** l'impronta SHA-256 di `breaklines`, `boundary` e `regioni_ponti` è invariata.

### Revisione: linee dei muri bloccate ed eccezioni

Dopo aver visto il risultato, l'utente ha deciso che:

* la N16000 resta così, come **eccezione**;
* anche la B13100 diventa un'**eccezione**;
* tutte le breakline che delimitano le regioni con `mat_id` 11 (le 20 strisce `muro` di Borgo, in 19 facce) devono restare **fisse**, cioè com'erano prima della correzione;
* le violazioni che restano le sistema lui a mano.

Le linee dei muri sono 32: quelle che condividono più di 1 cm con il contorno di una faccia di muro, compresi i piedi su cui i muri poggiano. La correzione ne aveva modificate 13.

Ripristinarle una per una non bastava: alcuni nodi condivisi con le linee vicine si erano spostati insieme a loro. Ho quindi rifatto la correzione dei 5 m con queste linee bloccate. Non vi si inseriscono vertici d'incrocio né d'innesto, non si toglie nessun vertice (nemmeno i due doppi già presenti sulla 893) e nessun loro nodo può essere spostato.

Ho riportato i sei file `_50m` allo stato di stamattina usando i backup del 17 novembre, verificati identici, e li ho riscritti. I punti regione, le sezioni e i file d'asse non cambiano rispetto alla versione precedente.

Le breakline modificate ora sono 533, e le 32 linee dei muri sono identiche byte per byte al backup. Restano **15 violazioni** su 1468 incroci:

* le eccezioni: N16000 (3.13 e 3.06 m) e B13100 (4.37 m);
* 12 nella zona dei muri di Borgo, da sistemare a mano:
  * B00000 (3.38 e 3.07 m);
  * B00050 (3.89 m);
  * B00100 (0.07 m);
  * B00150 (4.14 m);
  * B00250 (0.27 m);
  * B00350 (3.38 e 3.17 m);
  * B00400 (4.39 m);
  * B00450 (4.17 e 1.34 m);
  * B00500 (2.92 m).

  B00100 e B00250 hanno un vertice a pochi centimetri dall'incrocio e possono generare elementi molto piccoli.

Ho rifatto le verifiche sui file riletti dal disco, con lo stesso esito di prima. Sono cambiati solo il numero di violazioni (15) e quello delle breakline modificate (533). Il grafo ha sempre 902 facce, ognuna con il suo punto, e gli incroci sono tutti al loro posto.

### Questioni aperte

* **Regola dei 5 m.** Restano le 12 violazioni nella zona dei muri di Borgo (B00000–B00500), che l'utente sistema a mano. N16000 e B13100 sono eccezioni accettate.
* **B00200.** Non attraversa nessuna breakline, quindi non divide il letto: è solo una linea di controllo.
* **Mesh e modello.** La mesh va rigenerata dai file `_50m`. `STRINGDEF` deve elencare le 735 sezioni con i nuovi nomi; i vecchi nomi `S*****` e `V*****` non esistono più.

## 18 novembre 2026

### La richiesta

Mentre sistemava a mano le violazioni di Borgo, l'utente ha chiesto che la sezione **B00400 coincida esattamente con la nodestring `idrometro_Borgo`**. È il punto più importante del modello: lì anche nella realtà si misurano le portate (dai livelli) considerate più affidabili. Per arrivarci tutte le sezioni B vanno spostate verso monte dei circa 16 m che separavano le due linee, senza toccare N e V.

L'utente si aspettava due soli punti delicati, oltre alla zona interna di Borgo che sistema lui: i ponti Bordignon e Filippini. Secondo le sue misure, in entrambi i casi la sezione di valle non doveva finire dentro il ponte.

### Punto di partenza

* Breakline e punti regione erano quelli scritti il 17 novembre.
* Nel boundary l'utente aveva modificato in mattinata sette sezioni B: B00000, B00050, B00100, B00150, B00200, B00250 e B00350. Con lo spostamento queste modifiche si perdono, ma lo stato della mattina è conservato nei backup `*_backup_20261118.gpkg`.
* Le altre 53 nodestring erano identiche a quelle del 17. `idrometro_Borgo` ha due vertici ed è lunga 11.61 m.

### Lo spostamento

`idrometro_Borgo` incrocia la linea d'asse alla progressiva 16 655.68 m dell'asta, mentre la vecchia B00400 stava a 16 672.25 m: lo spostamento è di **16.57 m**.

Un primo tentativo con la programmazione dinamica libera, con la sola B00400 fissata, non andava bene. Dopo qualche chilometro la sequenza tornava sulle posizioni vecchie: 254 sezioni su 354 restavano dov'erano. L'ho scartato perché l'utente aveva chiesto di spostare tutto il ramo.

Ho quindi scritto `dpB2.py`. Ogni sezione ha come obiettivo la sua posizione vecchia meno 16.57 m e si sceglie tra i candidati entro 5 m dall'obiettivo, con un costo di 0.5 per metro di scarto e le stesse penalità di `dpB.py`. La B00400 è proprio la nodestring.

* **Curva stretta attorno alla progressiva 27 470 m.** Spostando tutto di 16.6 m, la coppia B11200–B11250 sta a cavallo della curva. Lungo la linea d'asse distano 50 m, in linea retta solo 47.85 m. Nessuna posizione entro 10 m dall'obiettivo rispetta anche la retta, quindi la distanza in linea retta è diventata una penalità e non più un vincolo rigido. La regola dei 50 ± 0.5 m resta rigida lungo la linea d'asse.
* **Fine del ramo.** Dopo lo spostamento ci sarebbe stato posto per una sezione in più in coda, ma sarebbe caduta a 12 m da `BC_brenta_valle`, ruotata di circa 30° e con il bankpoint destro sul bordo del dominio. Non l'ho aggiunta. Le sezioni B restano 354 e la B17650 sta ora 57.6 m a monte della fine della linea d'asse.

Risultato:

* spostamento tra 15.9 e 17.25 m;
* passo lungo la linea d'asse tra 49.75 e 50.5 m;
* B00000 alla progressiva 16 253.25 m dell'asta (era 16 269.75 m);
* nomi invariati, da B00000 a B17650. La B00400 sta a 402.43 m dall'inizio del ramo.

### I ponti

Nessuna sezione B attraversa una nodestring, tranne la B00400 che coincide con `idrometro_Borgo`. Nessuna cade dentro un ponte.

| Ponte | Sezione a monte | Sezione a valle |
|---|---|---|
| Bordignon | B00050, 24.2 m dal lato di monte | B00100, 20.4 m dal lato di valle |
| Filippini | B16950, 26.3 m dal lato di monte | B17000, 8.8 m dal lato di valle |

Le distanze sono quelle minime tra le linee. Le misure dell'utente erano corrette.

### Bankpoint

Ho rifatto la catena del 17 novembre con le nuove posizioni: `export_B.py` (ora accetta `dpB2.pkl`), `next_bed.py` (3 limiti), `obst.py` (66 limiti) e `bank.py`.

La B00400 è sostituita dalla nodestring in `assemble.py`. I suoi due bankpoint sono gli estremi di `idrometro_Borgo`, con `tipo` `nodestring` e `regola` `idrometro_Borgo`. Le quote lette dal DTM sono 379.763 m a sinistra e 378.068 m a destra.

Le sezioni N e V sono risultate identiche a quelle del 17.

### Regola dei 5 m e punti regione

Ho rifatto la correzione dei 5 m (`fix5.py`, con le 32 linee dei muri bloccate) partendo dalle breakline della mattina del 17, come il giorno prima. Il risultato:

* 535 breakline modificate. Rispetto al risultato del 17 ne cambiano 114, tutte lungo il ramo B;
* le 32 linee dei muri sono identiche al backup;
* nessun incrocio si è spostato.

Restano **11 violazioni su 1471 incroci**:

* l'eccezione N16000 (3.13 e 3.06 m);
* 9 nella zona dei muri di Borgo:
  * B00000 (1.47 m);
  * B00100 (2.34 e 1.05 m);
  * B00300 (2.23 e 2.47 m);
  * B00350 (2.21 m);
  * B00400 (3.57 m);
  * B00450 (2.89 m);
  * B00500 (1.43 m).

  Sei riguardano vertici delle linee dei muri, che sono bloccate. La B00450 riguarda un vertice fisso su una nodestring. Le due della B00300 sono state respinte dai controlli: lo spostamento avrebbe superato i 2 m, oppure avrebbe portato una linea troppo vicino a un punto regione. Quella della B00400 è un vertice della linea di muro 916, a 3.57 m dall'incrocio con `idrometro_Borgo`, quindi c'era già prima.

Con lo spostamento la B13100 non ha più violazioni, quindi l'eccezione non serve più.

Il grafo ha **901 facce**, una in meno del 17: la striscia tra la vecchia B00400 e `idrometro_Borgo` non esiste più. Ogni faccia ha un solo punto, tranne la coppia 57/58 già presente. Rispetto alla mattina del 17 sono stati tolti 55 punti nuovi e aggiunti 51. Tutti i punti originali sono presenti e non sono stati spostati.

### Scrittura e verifiche

Ho seguito questi passi:

1. ho copiato lo stato corrente dei sei layer in `*_backup_20261118.gpkg` e l'ho verificato con `cmp`;
2. ho riportato i layer ai backup del 17 mattina;
3. ho lanciato `write2.py`, che ha trovato i backup del 17 identici.

`verify2.py` sui file riletti dal disco ha dato questi risultati:

* 735 sezioni (N 321, V 60, B 354) con nomi consecutivi;
* le 53 nodestring identiche;
* sezioni coincidenti con i bankpoint;
* passo lungo la linea d'asse tra 49.75 e 50.5 m;
* nessun incrocio tra sezioni;
* un solo incrocio sezione-nodestring, cioè la B00400 sovrapposta a `idrometro_Borgo`;
* nessun incrocio con le breakline perso;
* integrità dei GeoPackage verificata;
* impronte degli originali invariate.

Gli altri due esiti segnalati sono quelli noti: le linee 987 e 1225 posate sulle sezioni e le 6 geometrie vuote delle breakline.

Ho rigenerato `docs/Brenta_sections_50m_mesh10.csv` con il nuovo script `sections_csv.py`. Prima di usarlo ho controllato che, applicato ai backup del 18, riproducesse la tabella del 17: le uniche differenze erano le lunghezze delle sette sezioni modificate a mano in mattinata.

### Questioni aperte

* **Regola dei 5 m.** Restano le 9 violazioni nella zona dei muri di Borgo (B00000–B00500), che l'utente sistema a mano. La N16000 resta un'eccezione.
* **Passo in linea retta B11200–B11250:** 47.85 m nella curva stretta, da confermare come eccezione al pari della N01900.
* **Fine del ramo B:** la B17650 sta a 57.6 m dalla fine della linea d'asse.
* **Mesh e modello.** La mesh va rigenerata dai file `_50m`, e `STRINGDEF` deve usare i nomi nuovi. La B00400 ha la stessa geometria di `idrometro_Borgo`, quindi va verificato come BASEmesh e BASEMENT trattano due nodestring coincidenti.

## 18 novembre 2026, pomeriggio: Borgo sistemato a mano, attributi ed eccezioni

### Cosa ha fatto l'utente

L'utente ha sistemato a mano in QGIS le sezioni nella zona dei muri di Borgo. Rispetto alla scrittura della mattina:

* sono cambiate 11 sezioni: B00000, B00050, B00150, B00200, B00250, B00300, B00350, B00400, B00450, B00500 e B00550;
* B00400 e `idrometro_Borgo` sono state allungate insieme verso destra (da 11.61 a 13.15 m) e restano coincidenti;
* molte sezioni ora terminano esattamente sulle linee dei muri o sulle nodestring degli edifici, invece di fermarsi 0.5 m prima;
* B00300 è stata spostata di circa 6 m: il suo punto d'asse è salito di 3.36 m;
* breakline e punti regione non sono cambiati.

### Centerpoint e bankpoint

Con il nuovo script `sync_cp_bp.py` ogni punto d'asse diventa l'intersezione della sezione con la linea d'asse del suo ramo. Da lì si ricalcolano `s_m`, `dist_next` e `dist_cp`. Un bankpoint il cui vertice si è spostato prende `tipo` e `regola` `manuale` e la quota della cella del DTM; per la B00400 diventa `nodestring`/`idrometro_Borgo`.

* **Bankpoint:** ne cambiano 20, tutti nelle sezioni modificate.
* **Punti d'asse:** cambiano B00300 (3.36 m), B00150, B00200, B00250, B00350, B00400 e B00500 (1–5 mm), più N00150 (2.5 cm) e N01950 (5 mm). Queste ultime due sono le sezioni modificate a mano prima del 17 novembre, che non passavano più esattamente per il loro punto d'asse.
* **Linea del ramo B:** non cambia, perché la B00000 incrocia l'asta nello stesso punto.

`write3.py` ha scritto i tre layer dopo i backup `*_backup_20261118b.gpkg` e ha letto 20 quote dal DTM.

### Controllo di tutti gli attributi e delle regioni

Il nuovo `verify3.py` controlla sui file riletti dal disco ogni attributo di boundary, linee d'asse, punti d'asse, bankpoint e punti regione. Alla prima esecuzione ha trovato quattro problemi, nati tutti dalle modifiche a mano:

1. **Quota della B00300.** Il primo vertice aveva z = 381.76, preso agganciandolo a `edificio_borgo_sx_2`. Le sezioni devono avere z = m = 0. Le quote diverse da 0 di `link_borgo_valle`, `edificio_borgo_sx_1`, `edificio_borgo_sx_2` e delle breakline 971, 1125, 1127 e 1135 ci sono già nei dati originali, e le ho lasciate.
2. **B00400.** Allungata, incrociava la breakline 895 a 2.0 mm dal nodo delle linee 894/895, cioè il vecchio estremo dell'idrometro.
3. **B00500.** Ruotata, incrociava la 895 a 1.2 mm da un suo vertice.

   Nei casi 2 e 3 la mesh avrebbe avuto un lato di un paio di millimetri.
4. **Punti regione.** Prolungando le sezioni fino ai muri si sono chiuse 5 nuove facce di letto tra B00100 e B00400, da 490 a 880 m², senza punto regione. Il grafo è passato da 901 a 906 facce.

Con il nuovo `fix_manual.py`, poi scritto da `write3.py` dopo i backup `*_backup_20261118c.gpkg`:

* ho portato a 0 la quota della B00300;
* ho spostato i due vertici di breakline sull'incrocio (2.0 e 1.2 mm), secondo la regola per cui si sposta la breakline e mai la nodestring. Nessuna delle due linee è un muro bloccato;
* ho aggiunto 5 punti `bed_borgo` (`mat_id` 13, `max_area` 5, fid 972–976) nel polo di inaccessibilità di ogni faccia, a 4.9–7.1 m dai bordi. Gli attributi vengono dalla regione originale del luogo, il fid 134.

Ho poi rilanciato `sync_cp_bp.py`, che non ha trovato nulla da cambiare, e i controlli.

**Esito finale di `verify3.py` e `verify3_dtm.py`**

* **Conteggi:** 53 nodestring e 735 sezioni con nomi, fid e id regolari; 735 punti d'asse, 1470 bankpoint, 3 linee d'asse e 909 righe di punti regione.
* **Sezioni:** sono tutte a due vertici, con z = 0 e orientate da sinistra a destra. Nessuna incrocia un'altra sezione.
* **Contatti con le nodestring:** la B00400 coincide con `idrometro_Borgo`. B00150, B00200, B00250, B00300 e B00350 terminano su una nodestring di edificio senza attraversarla.
* **Punti d'asse:** stanno tutti sulla loro sezione e sulla linea d'asse, con `s_m` e `dist_next` coerenti.
* **Bankpoint:** coincidono tutti con i vertici delle sezioni. `s_m`, `dist_cp`, `tipo`, `regola` e `prom` sono coerenti, e `z_dtm` è uguale alla cella del DTM per tutti i 1470 punti, con differenza massima 0.
* **Tipi di bankpoint:**
  * `max` 1028 (713 `mid`, 315 `toe15`);
  * `fallback` 419;
  * `manuale` 21 (19 a Borgo, più N00150 sx e N01950 sx);
  * `nodestring` 2 (B00400).
* **Punti regione:**
  * 906 facce, ognuna con un punto, tranne la coppia 57/58 già presente; nessun punto fuori dalle facce;
  * geometrie nulle solo ai fid 65 e 135, come negli originali;
  * i punti originali sono presenti, non spostati e con gli stessi attributi, tranne il 41 sostituito il 9 novembre;
  * nessun attributo nullo e nessuna combinazione di attributi che non esista negli originali;
  * a meno di 1 m dalle linee ci sono solo punti originali nelle strisce dei muri;
  * l'unico nuovo punto con un nome diverso da quello della regione originale nello stesso luogo è il 504, sistemato dall'utente il 17.
* **GeoPackage:** l'integrità è a posto e le impronte degli originali sono invariate.
* **Rimasto fuori dalle eccezioni:**
  * **11 incroci a Borgo con un vertice di una linea dei muri entro 5 m:** B00000 (1.47 m), B00100 (2.34 e 1.05 m), B00150 (2.47 m), B00200 (2.18 m), B00300 (3.21, 0.87 e 0.87 m), B00400 (3.57 m), B00450 (2.89 m) e B00500 (1.42 m). Quei vertici sono bloccati;
  * **tre passi lungo la linea d'asse oltre i 50.5 m di 4–5 mm:** N01950–N02000, B00150–B00200 e B00450–B00500.

  Nessun altro incrocio ha vertici entro 5 m.

Ho rigenerato `docs/Brenta_sections_50m_mesh10.csv` con `sections_csv.py`.

### Eccezioni

L'utente ha fissato l'elenco delle eccezioni, che comprende tutte e sole queste sezioni:

* **regola dei 5 m:** N16000;
* **passo tra sezioni:**
  * N01900–N01950 (46.68 m in linea retta);
  * B11200–B11250 (47.85 m in linea retta);
  * B00250–B00300–B00350, perché la B00300 è stata spostata a mano (47.14 e 53.61 m lungo la linea d'asse).

La B13100 non è più un'eccezione. Le stesse eccezioni sono scritte in `verify3.py` e in `dx_dev.py`.

### Revisione: incroci vicini ai muri accettati come eccezioni

L'utente ha accettato come eccezioni della regola dei 5 m gli 11 incroci di Borgo che hanno un vertice di una linea dei muri entro 5 m. Riguardano le sezioni B00000, B00100, B00150, B00200, B00300, B00400, B00450 e B00500. La categoria della regola dei 5 m comprende quindi la N16000 e queste otto sezioni; la categoria del passo resta invariata.

Ho aggiornato le eccezioni in `verify3.py` e in `dx_dev.py`. `verify3.py` ora conferma che gli incroci entro 5 m sono esattamente quelli delle eccezioni. Resta segnalato solo il controllo del passo, per le tre coppie a 50.504–50.505 m.

### Analisi statistica del passo tra le sezioni

L'analisi del passo tra sezioni consecutive (analisi 1 su dx_dev, analisi 2 su dx_dev_abs), con tabelle e figure, è in [Brenta_analisi_passo_50m.md](Brenta_analisi_passo_50m.md).

### Questioni aperte

* **Passi di 50.504–50.505 m** lungo la linea d'asse in N01950–N02000, B00150–B00200 e B00450–B00500: superano la tolleranza di 4–5 mm per effetto delle modifiche a mano.
* **Mesh e modello.** La mesh va rigenerata dai file `_50m` e `STRINGDEF` va aggiornato. Va anche verificato come BASEmesh tratta la B00400 coincidente con `idrometro_Borgo` e le sezioni che terminano sulle nodestring degli edifici.

## 19 novembre 2026

### Documentazione allineata

In `Brenta_regole_e_metodo.md` due dati non erano aggiornati: le righe di `regioni_ponti_50m`, ferme a 905, e il numero di sezioni nel CSV, indicato come 737 invece di 735. Li ho corretti.

### Punti regione: controllo e pulizia

L'utente ha chiesto di tenere in `regioni_ponti_50m` solo i punti con geometria valida e di controllare che ci sia un solo punto per regione e che il layer si possa usare direttamente per la mesh.

Per il controllo ho scritto `check_regions.py`, che costruisce il grafo planare in modo diverso da `verify3.py`:

* noding con `shapely.node`;
* eliminazione dei segmenti sovrapposti;
* aggancio esplicito a 1 mm delle estremità che toccano il tratto interno di un'altra linea.

Questi innesti a T sono 206. Le estremità distano dalla linea 10⁻¹¹–10⁻⁹ m e, se non si collegano, il grafo risulta aperto e diverse regioni si fondono. Una prima versione dello script, senza l'aggancio, dava infatti risultati sbagliati.

Sul layer del 18 novembre l'esito è stato questo:

* 909 righe: 907 punti e i due fid 65 e 135 senza geometria;
* nessun punto con geometria non valida o con Z, e nessun attributo nullo;
* una sola faccia con due punti, la 57/58 (`muro`, attributi identici);
* i 20 punti con `buco` uguali agli originali.

Decisione dell'utente: eliminare i fid 65, 135 e 58.

Con il nuovo `drop_regions.py` ho fatto il backup `regioni_ponti_50m_backup_20261119.gpkg`, verificato identico al file di partenza, e ho eliminato le tre righe in un'unica transazione.

### Verifiche (sul file riletto dal disco)

1. **Conteggi e struttura:** 906 righe, tutte con geometria `Point`, EPSG:25832, campi invariati. `integrity_check` ok, indice R-tree e `gpkg_ogr_contents` a 906.
2. **Righe rimaste:** identiche al backup per geometria e attributi. Mancano solo i fid 58, 65 e 135.
3. **Grafo (`check_regions.py`):** 911 facce, di cui 906 con un punto ciascuna. Nessuna faccia ha più di un punto e nessun punto cade fuori dalle facce.
4. **Facce senza punto:** sono 5 strisce larghe meno di un micrometro, non regioni vere (vedi più sotto).
5. **Robustezza:** con le coordinate delle linee arrotondate a 1 mm e a 1 cm nessun punto cambia faccia.
6. **Distanza dalle linee:** 26 punti stanno a meno di 1 m da una linea. Sono tutti originali, nelle strisce dei muri e del pilone; il minimo è 0.35 m.
7. **Originali:** le impronte SHA-256 di `breaklines`, `boundary` e `regioni_ponti` sono invariate.

In `verify3.py` ho aggiornato i valori attesi: nessuna faccia con più punti e nessuna riga senza geometria. Il file `mat11_lines.json` non c'era più, quindi ho ricostruito l'elenco delle 32 linee dei muri dai backup del 17 novembre, con la stessa logica di `prep_inputs_nvb.py`.

Rilanciato, `verify3.py` dà 906 facce, ognuna con un punto. I punti regione, gli attributi e l'integrità dei sei GeoPackage sono a posto. L'unico controllo segnalato è quello del passo, per le tre coppie note a 50.504–50.505 m.

### Strisce alle chiusure dei ponti

Le 5 facce senza punto stanno dove le breakline di chiusura dei ponti, prolungate il 9 novembre fino ai nuovi cigli, corrono accanto alle nodestring dei ponti a circa 10⁻⁸ m di distanza:

* 1113 lungo `P17_monte` (due strisce);
* 1116 lungo `P20_valle`;
* 1118/1124 lungo `P27_valle`;
* 1421 lungo `P13_monte_idrometro_Ponte_Cervia`.

Negli originali non ci sono. La mesh del 10 novembre (`mesh/10_quality-mesh.2dm`, 790 nodestring, quindi costruita sulla geometria del 9 novembre) le ha già incontrate: in quei punti non ha elementi anomali, con area minima da 1.6 a 2.4 m² e 0.10 m² a P13. Dalla stessa mesh si vede che i punti con `buco` sono trattati come buchi, perché il materiale 0 non compare.

### Breakline dei ponti sovrapposte alle nodestring

Su richiesta dell'utente ho eliminato le 5 strisce. In origine ogni breakline di chiusura era una copia esatta della nodestring del ponte, con gli stessi due vertici. Il 9 novembre è stata prolungata oltre i due estremi. In seguito il tratto in comune ha perso i vertici della nodestring e ha preso vertici intermedi a 10⁻¹¹–10⁻¹⁰ m da essa.

Con il nuovo `fix_bridges.py`:

* nel tratto in comune, le breakline 1113 (`P17_monte`), 1116 (`P20_valle`), 1118 (`P27_valle`) e 1421 (`P13_monte_idrometro_Ponte_Cervia`) hanno ora esattamente i due vertici della nodestring, senza vertici intermedi. I prolungamenti sono invariati;
* la 1124, che tocca solo l'estremo di `P27_valle`, ha quel vertice portato esattamente sull'estremo;
* le nodestring non sono state toccate.

Il vertice tolto alla 1113 nel punto dove arrivano le breakline 567 e 1050 rende quelle due linee un innesto a T, a 5·10⁻¹¹ m dal tratto. È la stessa situazione dei dati originali.

Prima di scrivere ho controllato che:

* lo spostamento massimo fosse 3.5·10⁻¹⁰ m;
* non nascessero nuovi incroci;
* nessun punto regione si avvicinasse alle linee;
* nessuna delle linee fosse fra quelle dei muri bloccate.

Ho anche fatto una prova del grafo su una copia. Poi `write3.py` ha scritto le 5 geometrie dopo il backup `breaklines_50m_backup_20261119b.gpkg`.

### Verifiche (sui file riletti dal disco)

1. **Breakline:** cambiate solo le 5 indicate. Fid e attributi sono invariati, ognuna resta in una sola parte, e i vertici delle nodestring sono presenti esattamente.
2. **`check_regions.py`:** 906 facce, nessuna striscia, nessuna faccia senza punto o con più punti. Il risultato è identico con le coordinate arrotondate a 1 mm e a 1 cm.
3. **`verify3.py`:** 906 facce con un punto ciascuna. Per la regola dei 5 m restano solo le eccezioni note. Gli incroci delle sezioni e l'integrità dei GeoPackage sono invariati. L'unico controllo segnalato resta quello del passo, per le tre coppie a 50.504–50.505 m.
4. **Originali:** le impronte SHA-256 sono invariate.

## 19 novembre 2026, sera: allineamento dopo la mesh definitiva

Per generare la mesh definitiva l'utente ha modificato a mano in QGIS 8 sezioni: V01050, V02950, B00000, B00250, B00450, B00950, B07700 e B12600. Ha anche modificato 30 breakline e la nodestring `P13_monte_idrometro_Ponte_Cervia`. Breakline, boundary e punti regione non sono stati toccati da me (impronte SHA-256 uguali prima e dopo).

### Centerpoint, bankpoint e linee d'asse

`sync_cp_bp.py` ha confrontato le sezioni con i layer salvati:

* **bankpoint:** ne cambiano 8, uno per sezione modificata, tutti con `tipo` e `regola` `manuale`. Gli spostamenti vanno da 0.02 m (B00950 dx) a 5.58 m (B12600 sx);
* **B00000:** si è spostata di 0.48 m verso monte lungo l'asta (s0_asta da 16 253.250 a 16 252.770 m). La linea d'asse B è stata ritagliata di nuovo, e `s_m` di tutte le sezioni B è aumentato di 0.48 m;
* **centerpoint:** si spostano di qualche millimetro o centimetro quelli delle sezioni modificate (al massimo 3.9 cm, V02950; 0.48 m la B00000 lungo l'asta).

`write3.py` ha scritto linee d'asse, centerpoint e bankpoint dopo il backup `*_backup_20261119c.gpkg` e ha letto dal DTM le 8 quote nuove. Rilanciato, `sync_cp_bp.py` dà zero cambiamenti. Ho anche rigenerato `docs/Brenta_sections_50m_mesh10.csv`.

### Eccezioni

Su indicazione dell'utente ho aggiunto alle eccezioni (in `verify3.py`, `dx_dev.py` e al §14 bis delle regole):

* **regola dei 5 m:** N02150 (nodo delle breakline 210 e 1232 a 1.00 m dall'incrocio) e B12600 (estremi a 1.5 mm e 0.2 mm da un vertice delle breakline 1316 e 1317);
* **passo:** V01050–V01100 (50.517 m), B00450–B00500 (50.502 m) e B00900–B00950 (50.509 m), dovute alle sezioni modificate.

Le altre sezioni modificate non hanno bisogno di eccezioni: V02950, B07700 rispettano tutte le regole, mentre B00000, B00250 e B00450 lo erano già (per B00000 e B00450 sono cambiate le distanze dai vertici dei muri: 2.34 m e 1.26/2.89 m).

### Verifiche (sui file riletti dal disco)

1. **`verify3.py`:** conteggi, nomi, geometrie delle sezioni, linee d'asse, centerpoint e bankpoint corretti; 906 facce con un punto ciascuna; integrità dei sei GeoPackage a posto. Restano segnalati:
   * il passo di N01950–N02000 (50.505 m) e B00150–B00200 (50.504 m), già noti;
   * la regola dei 5 m alla N15150: il nodo comune alle breakline 866 e 1151, modificate dall'utente, sta a 3.86 m dall'incrocio. Non l'ho aggiunta alle eccezioni senza conferma.
2. **`verify3_dtm.py`:** le 1470 quote dei bankpoint coincidono con il DTM.
3. **Impronte SHA-256:** invariate per breaklines_50m, boundary_50m, regioni_ponti_50m e per gli originali.

### Mesh definitiva: lati minuscoli alla B12600

Agli estremi della B12600 la mesh (`10_quality-mesh.2dm` e `10_computational-mesh.2dm`, 519 726 nodi) ha nodi a 0.2 mm e circa 1.5 mm l'uno dall'altro: il lato più corto di tutta la mesh è 0.2 mm. Nascono perché gli estremi della sezione cadono vicinissimi, ma non sopra, a un vertice delle breakline 1316 e 1317. In BASEMENT un lato così corto può ridurre molto il passo temporale.

### Analisi del passo

Ho rilanciato `dx_dev.py` e `dx_dev_fig.py` e aggiornato [Brenta_analisi_passo_50m.md](Brenta_analisi_passo_50m.md). Le coppie escluse passano da 19 a 27. Con tutte le coppie i risultati quasi non cambiano (dx_dev_abs 0.1641). Senza eccezioni dx_dev_abs vale 0.0854, e nel ramo N il caso peggiore diventa N01550–N01600 (0.045), perché N02100–N02150 ora è esclusa.

## 19 novembre 2026, sera: B12600 corretta ed eccezioni definitive

L'utente ha corretto le breakline 1316 e 1317 alla B12600 e rigenerato la mesh. Ho controllato i layer:

* le sezioni non sono cambiate: `sync_cp_bp.py` dà zero cambiamenti per centerpoint e bankpoint;
* la B12600 non ha più vertici di breakline entro 5 m dagli incroci, quindi l'ho **tolta dalle eccezioni**;
* `check_regions.py` dà 906 facce con un punto ciascuno, senza strisce, anche con le coordinate arrotondate a 1 mm e 1 cm.

**Nota:** i file `mesh/10_quality-mesh.2dm` e `mesh/10_computational-mesh.2dm` presenti sul disco sono ancora quelli delle 16:28 e 16:32 e hanno ancora i lati di 0.2 mm alla B12600. La mesh rigenerata non è ancora stata salvata in quella cartella.

Su indicazione dell'utente ho aggiunto alle eccezioni tutte le osservazioni ancora aperte:

* **regola dei 5 m:** N15150 (3.86 m, breakline 866 e 1151);
* **passo:** N01950–N02000 (50.505 m) e B00150–B00200 (50.504 m).

### Verifiche (sui file riletti dal disco)

1. **`verify3.py`:** tutti i controlli `OK`; le violazioni del passo e della regola dei 5 m sono esattamente le eccezioni.
2. **`verify3_dtm.py`:** le 1470 quote dei bankpoint coincidono con il DTM.
3. **Analisi del passo:** l'ho rilanciata con le eccezioni definitive. Le coppie escluse restano 27: entrano N15100–N15150 e N15150–N15200, ed escono B12550–B12600 e B12600–B12650. Senza eccezioni dx_dev_abs resta 0.0854.

