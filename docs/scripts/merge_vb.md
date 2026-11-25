# merge_vb.py

Settimo passo (2026-11-24). Porta le sezioni da tre rami (N, V, B) a due (V, B).

* **V:** le sezioni restano uguali. La nodestring `divergenza_valle_brenta_vecchio` viene rinominata **V00000** e diventa la prima sezione del ramo:
  * il centerpoint è l'incrocio con la linea d'asse V, prolungata all'indietro fino alla nodestring (2.356 m);
  * i bankpoint sono i due estremi della nodestring, con `tipo` `nodestring` e `regola` `V00000`;
  * tutte le progressive V crescono di 2.356 m.
* **B:** un solo ramo da Caldonazzo a valle.
  * **Vecchie N:** sono spostate tutte della stessa quantità DELTA verso monte, quindi il passo tra loro non cambia. DELTA = 27.23 m, scelto in modo che la vecchia N16050 cada 150 m a monte della vecchia B00000.
  * **Due sezioni nuove:** stanno tra la vecchia N16050 e la vecchia B00000, con passo di 50 m esatti.
  * **Vecchie B:** mantengono geometria e attributi; cambiano solo il nome e la progressiva.
  * **Nomi:** B00000 è la prima sezione, poi posizione × 50.

Le sezioni spostate e quelle nuove si ricalcolano con il metodo della skill `river-cross-sections`:
* centro sulla linea d'asse e direzione perpendicolare alla corda tra s − 1 e s + 1 m;
* distanze da piedi e cigli misurate sui layer derivati attuali;
* bankpoint con `next_bed.py`, `obst.py` e `bank.py` della skill.

## Requisiti

* Interprete: `python3` di Anaconda (`~/anaconda3/bin/python3`).
* Importa `common.py` e `geom.py` da `skills/river-cross-sections/scripts/`.

## Input

* Argomento 2: la cartella dei layer del progetto (`layers`). La legge soltanto.
* Argomento 3: una cartella di lavoro della skill (WD), con `rcs_config.json`, `layers/` e `work/`. Il calcolo dei bankpoint richiede in `WD/layers/` una copia di `boundary_50m` **senza le sezioni**, come nella pipeline originale.
* Layer usati:
  * `boundary_50m`, `breaklines_50m`, `regioni_ponti_50m`, `centerpoints_50m`, `bankpoints_50m`, `centerline_50m`;
  * `centerline_50m_backup_20261117` (linea `asta_principale`, con s = 0 al BC di Caldonazzo).

## Sottocomandi e output

1. `prep layers WD` scrive due file:
   * `WD/work/sec_in.json`: le 323 stazioni nuove del ramo B;
   * `WD/work/check_in.json`: le stazioni N attuali, per la verifica.
2. Sulla WD si lanciano `next_bed.py`, `obst.py` e `bank.py` della skill, che producono `work/bank_out.json`.
3. `assemble layers WD` scrive:
   * `WD/work/merge_payload.json`, con `secs`, `rename`, `cl`, `cp` e `bp`, per `write3.py` della skill;
   * `near_nodes.json` e `secs_new.json`, per `regions2.py` della skill.
4. Si lancia `regions2.py` della skill.
5. `regions layers WD` aggiunge al payload `reg_drop` e `reg_new`. Applica solo i cambiamenti dei punti regione **causati dalle sezioni**, cioè quelli delle facce che confinano con una sezione ricalcolata o tolta. Gli altri cambiamenti li stampa e non li applica.
6. `write3.py` della skill scrive i layer, con backup etichettati.

## Uso (24 novembre 2026)

```bash
~/anaconda3/bin/python3 scripts/merge_vb.py prep layers WD
```

```bash
cd WD; cp work/sec_in.json work/sec_in_new.json; cp work/check_in.json work/sec_in.json
```

Poi si lanciano `next_bed`, `obst` e `bank` e si confronta il risultato con i bankpoint N consegnati, come verifica. Dopo si ripete con `sec_in_new.json`.

```bash
~/anaconda3/bin/python3 scripts/merge_vb.py assemble layers WD
```

```bash
(cd WD && ~/anaconda3/bin/python3 skills/river-cross-sections/scripts/regions2.py)
```

```bash
~/anaconda3/bin/python3 scripts/merge_vb.py regions layers WD
```

```bash
(cd WD2 && /usr/bin/python3 skills/river-cross-sections/scripts/write3.py work/merge_payload.json 20261124a)
```

Per scrivere si usa una seconda WD, la cui cartella `layers` è un collegamento a `layers/` del progetto, così i backup finiscono accanto ai layer. La configurazione della skill per lo stato V/B è salvata in `docs/rcs_config_brenta_vb.json`.

## Verifiche

* **Verifica del metodo:** con le stazioni N attuali, 636 bankpoint su 642 tornano uguali entro 1 cm. Le differenze sono N00150 sx e N01950 sx (modificati a mano), N16050 dx (prolungamento nel canale di destra) e tre scarti di 1–5 cm.
* **Sezioni ricalcolate:** ognuna delle 323 incrocia esattamente due breakline (i piedi), nessuna nodestring e nessun'altra sezione.

## Limiti

* Le sezioni N modificate a mano (N00150 sx, N01950 sx) e il prolungamento della N16050 nel canale di destra sono sostituiti dalla regola: vanno rivisti a mano se servono.
* Le breakline non vengono toccate: la regola dei nodi vicini va riapplicata attorno ai nuovi incroci.
* Le eccezioni non vengono rinominate.
