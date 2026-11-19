# verify3.py

Quarto passo (2026-11-18). Controlla in modo indipendente **tutti gli attributi** e le geometrie dei sei layer `_50m`, riletti dal disco. È pensato per essere lanciato dopo ogni modifica, a mano o con gli script. Non scrive nulla. Le quote dei bankpoint sul DTM si controllano a parte con `verify3_dtm.py`.

## Requisiti

* Interprete: `python3` di Anaconda (geopandas, shapely 2.1, numpy, scipy).

## Input

* Argomento 1: `mat11_lines.json` (`prep_inputs_nvb.py`), le breakline dei muri, che sono bloccate.
* La cartella `layers` (percorso assoluto fisso) con:
  * i sei `*_50m.gpkg`;
  * l'originale `regioni_ponti.gpkg`, per gli attributi e i punti con fid ≤ 176;
  * gli originali `breaklines.gpkg` e `boundary.gpkg`, per il grafo originale;
  * `centerline_50m_backup_20261117.gpkg`, per l'asta intera che fa da riferimento alla progressiva B.

## Output

Solo stampa: una riga numerata per controllo, che termina con `OK` o `**CHECK**` e riporta gli elementi in difetto.

## I controlli

* **(A) Boundary**
  * conteggi: 53 nodestring e 735 sezioni;
  * nomi delle sezioni consecutivi per ramo e nell'ordine N, V, B;
  * nomi e id unici, fid delle sezioni da 64 e id da 60;
  * ogni sezione in una sola parte, con 2 vertici e z = 0.
* **(B) Linee d'asse**
  * `lung_m` uguale alla lunghezza della geometria;
  * `s0_asta` della linea B uguale alla progressiva della B00000 sull'asta, e la linea B comincia sulla B00000.
* **(C) Centerpoint**
  * uno per sezione, con lo stesso nome e `stream` uguale alla lettera del ramo;
  * il punto sta sulla sezione e sulla linea d'asse, e `s_m` è la sua progressiva nel ramo;
  * `dist_next` è coerente, nullo per l'ultima sezione di ogni ramo.
* **(D) Bankpoint**
  * due per sezione, con `sezione` giusto, coincidenti con i vertici (sinistro per primo);
  * `s_m` uguale a quello del centerpoint e `dist_cp` uguale alla distanza da esso;
  * `tipo` in un insieme ammesso; `prom` ≥ 0.05 solo per `max` e nullo negli altri casi; `manuale`/`manuale`, `muro`/`muro`, `nodestring` con un estremo della nodestring;
  * `z_dtm` non nullo;
  * la sezione va da sinistra a destra rispetto al verso della linea d'asse.

  La stampa include il conteggio per tipo e regola e l'elenco dei bankpoint `manuale` e `nodestring`.
* **(E) Passo e regola dei 5 m**
  * passo lungo la linea d'asse e distanza in linea retta fuori da 50 ± 0.5 m (tolleranza numerica 1e-6 m), confrontati con le eccezioni;
  * incroci con un vertice di breakline entro (1 mm, 5 m), divisi in tre gruppi: eccezioni, vertici delle linee dei muri bloccate e altri vertici. Gli altri vertici devono essere zero;
  * numero di breakline attraversate da ogni sezione.
* **(F) Incroci**
  * nessun incrocio tra sezioni;
  * i contatti con le nodestring sono di tre tipi: `equal` (B00400 = `idrometro_Borgo`), `section end on nodestring` (estremo appoggiato su un edificio) e `cross`, che non deve comparire.
* **(G) Punti regione**
  * un punto per faccia del grafo planare (breakline e tutto il boundary), senza eccezioni (il doppione 58 e le righe senza geometria 65 e 135 sono stati eliminati il 2026-11-19); nessun punto fuori dalle facce; nessuna riga con geometria nulla;
  * i punti originali con fid ≤ 176 presenti, non spostati e con gli stessi attributi, tranne il 41 sostituito il 9 novembre;
  * nessun attributo nullo e nessuna combinazione `nome`/`mat_id`/`max_area`/`buco` che non esista negli originali;
  * punti a meno di 1 m dalle linee: solo originali, nelle strisce strette dei muri;
  * nuovi punti il cui nome non coincide con la regione originale nello stesso luogo, come diagnostica.
* **(H) GeoPackage:** `integrity_check`, voci dell'R-tree, sistema di riferimento 25832 e tipo di geometria.

## Eccezioni

Le eccezioni sono scritte nel codice, come deciso dall'utente il 18 novembre:

* **regola dei 5 m:** N16000, più B00000, B00100, B00150, B00200, B00300, B00400, B00450 e B00500, il cui vertice vicino appartiene a una linea dei muri bloccata (`EXCW`);
* **passo:** le coppie N01900–N01950, B11200–B11250, B00250–B00300 e B00300–B00350.

## Uso

```bash
python3 scripts/verify3.py /percorso/WD/mat11_lines.json
```

```bash
/usr/bin/python3 scripts/verify3_dtm.py
```

## Esito del 18 novembre

Tutti i controlli danno `OK` tranne il 15. Le anomalie di passo comprendono, oltre alle eccezioni, tre coppie che superano i 50.5 m lungo la linea d'asse di 4–5 mm: N01950–N02000, B00150–B00200 e B00450–B00500.

Il punto 17 elenca 11 incroci che hanno un vertice delle linee dei muri entro 5 m. Dopo che l'utente li ha accettati come eccezioni, il controllo verifica che siano esattamente quelli dell'elenco e dà `OK`. Il punto 25 segnala solo il punto 504, già sistemato dall'utente il 17 novembre.
