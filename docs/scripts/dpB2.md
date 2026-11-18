# dpB2.py

Terzo passo (2026-11-18). Sposta verso monte tutto il ramo B, in modo che la sezione B00400 coincida esattamente con la nodestring `idrometro_Borgo`. È il punto dove a Borgo si misurano le portate più affidabili del modello. Precedente: `dpB.py`, di cui usa il risultato come riferimento; successivo: `export_B.py WD dpB2.pkl`, poi `next_bed.py`, `obst.py`, `bank.py` e `assemble.py`.

## Requisiti

* Interprete: `python3` di Anaconda (numpy, scipy, shapely, geopandas).
* Modulo importato: `core.py` da `WD/work` (`SP`, `pickle`, `np`).
* Lo script va copiato in `WD/work`.

## Input

* Argomento 1: la cartella di lavoro `WD`.
* Argomento 2: il file boundary che contiene la nodestring di ancoraggio, di norma `WD/in/boundary_50m.gpkg`.
* `WD/work/cands.pkl` (`place.py`): candidati dell'asta (`main`) ogni 0.25 m, con penalità e flag.
* `WD/work/dpB.pkl` (`dpB.py`): la disposizione del 17 novembre (chiave `B`) e gli indici di N e V, ricopiati senza modifiche.
* `WD/xn_points.json` (`prep_inputs_nvb.py`): punti di incontro tra nodestring e breakline.

## Output

* `WD/work/dpB2.pkl`, un dizionario con:
  * `N`, `V`: copiati da `dpB.pkl`;
  * `B`: indici dei candidati del ramo B. Nella posizione della sezione ancorata c'è il candidato più vicino, che fa solo da segnaposto;
  * `anchor`: `k` (posizione nel ramo, 8 = B00400), `nome`, `s` (progressiva dell'asta), `x`, `y` (intersezione della nodestring con la linea d'asse), `nx`, `ny` (normale unitaria verso l'estremo sinistro), `tL`, `tR` (distanze dei due estremi dal centro) e `coords` (i due vertici, sinistro per primo).
* La stampa riporta:
  * spostamento, progressiva dell'ancora, numero di sezioni, prima e ultima sezione;
  * passo e corda minimi e massimi, scarto dagli obiettivi;
  * sezioni con distanza in linea retta fuori da 49.5–50.5 m e sezioni a più di 0.13 m dall'obiettivo;
  * somme delle penalità.

## Parametri e costanti

* `ANCHOR_K = 8` e `ANCHOR_NAME = 'idrometro_Borgo'`: la sezione ancorata e la nodestring. La nodestring deve avere 2 vertici e incrociare la linea d'asse una sola volta.
* `S_BRIDGE = 16327.97` e `MARGIN = 5`: come in `dpB.py`, nessuna sezione tra 5 m a monte di `Ponte_Bordignon_monte` e 20 m a valle.
* `WIN = 5` m: finestra di ricerca attorno a ogni obiettivo.
* `W_DEV = 0.5`: costo per metro di scarto dall'obiettivo.
* `ADD_END = False`: se fosse vero, aggiungerebbe una sezione in coda quando l'ultima resta a più di 50.5 m dalla fine della linea d'asse. Non è usato: sul Brenta quella sezione cadrebbe 12 m a monte di `BC_brenta_valle`, ruotata di circa 30° e con il bankpoint destro sul bordo del dominio.
* Le altre penalità sono quelle di `dpB.py`: `pen5`, `hitO` (+1000), `hitB` (+10000), +50 per un piede a meno di 5 m da un punto di `xn_points.json`, candidati non validi esclusi.

## Uso

```bash
cp scripts/dpB2.py /percorso/WD/work/
```

```bash
python3 /percorso/WD/work/dpB2.py /percorso/WD /percorso/WD/in/boundary_50m.gpkg
```

Poi:

```bash
python3 /percorso/WD/work/export_B.py /percorso/WD dpB2.pkl
```

(layout di `WD`: vedi [dpB.md](dpB.md), sezione Uso.)

## Funzionamento

1. Calcola le penalità dei candidati come `dpB.py`.
2. Interseca la nodestring con la polilinea dei centri dei candidati. Ricava così la progressiva `s_a` (16655.68 m) e il centro della sezione ancorata, e ordina i vertici con il sinistro per primo.
3. Calcola lo spostamento `D = s(B00400 vecchia) − s_a`, pari a 16.57 m. L'obiettivo della sezione k è `t_k = s_vecchia_k − D`. L'ancora è un nodo fisso, senza penalità.
4. Svolge una programmazione dinamica a strati, uno strato per sezione. In ogni strato i candidati validi stanno entro `WIN` dall'obiettivo. Il costo di un candidato è la sua penalità più `W_DEV` per metro di scarto. Il passo tra due sezioni consecutive deve stare tra 49.5 e 50.5 m lungo la linea d'asse, ed è un vincolo rigido. Una distanza in linea retta fuori da 49.5–50.5 m costa invece 500 + 100·|corda − 50|, perché la regola dei 50 m si misura lungo la linea d'asse e nelle curve strette la retta può risultare più corta.
5. Ricostruisce il percorso migliore, rimette il segnaposto nella posizione dell'ancora e salva.

## Verifiche e limiti

* Risultato del 18 novembre:
  * 354 sezioni, B00000 a s = 16253.25 dell'asta e B17650 a 17670.25 m nel ramo B;
  * spostamento tra 15.9 e 17.25 m;
  * passo tra 49.75 e 50.5 m;
  * una sola distanza in linea retta fuori tolleranza: B11200–B11250, 47.85 m nella curva stretta attorno a s ≈ 27 470 m.
* In quella curva lo spostamento rigido non trova coppie con la distanza in linea retta entro 49.5–50.5 m anche allargando la finestra a 10 m. Per questo la corda è un vincolo morbido.
* Il risultato va letto con le verifiche geometriche (`check_geom.py`, `verify2.py`). In particolare si controlla che nessuna sezione attraversi una nodestring, tranne la B00400 che coincide con `idrometro_Borgo`, e che nessuna cada dentro un ponte.
* I valori di `S_BRIDGE`, `ANCHOR_K` e `ANCHOR_NAME` sono fissi nel codice.
