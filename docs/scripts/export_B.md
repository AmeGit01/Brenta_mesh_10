# export_B.py

Secondo passo (2026-11-17), aggiornato il 2026-11-18. Scrive `sec_in.json` per il solo ramo B, con gli stessi campi di `export_sec.py`, a partire dagli indici scelti da `dpB.py` o, dal 18 novembre, da `dpB2.py`. Precedente: `dpB.py` o `dpB2.py`; successivo: `next_bed.py`, poi `obst.py` e `bank.py`.

## Requisiti

* Interprete: `python3` di Anaconda.
* Modulo importato: `core.py` da `WD/work` (`SP`, `pickle`, `np`); `json`.
* Lo script va copiato in `WD/work`.

## Input

* `WD/work/cands.pkl` (`place.py`): chiave `main` con `ss`, `P`, `n`, `tL`, `tR`, `cL`, `cR`.
* Argomento 2 (facoltativo): nome del file in `WD/work` da leggere, `dpB.pkl` se assente. Dal 18 novembre si usa `dpB2.pkl`.
* `WD/work/dpB.pkl` (`dpB.py`) o `WD/work/dpB2.pkl` (`dpB2.py`): chiave `B` e, solo per `dpB2.pkl`, chiave `anchor`.

## Output

* `WD/work/sec_in.json` (**sovrascritto**): lista di dizionari `stream='main'`, `tag='B'`, `s`, `x`, `y` (centerpoint), `nx`, `ny` (normale unitaria, positiva verso sinistra), `tL`, `tR` (distanze del piede), `cL`, `cR` (distanze del ciglio), in metri.
* Con `dpB2.pkl` il record della sezione ancorata (B00400) contiene anche la chiave `anchor`, con la geometria di `idrometro_Borgo`. Gli altri campi restano quelli del candidato più vicino, che fa solo da segnaposto: così `next_bed.py`, `obst.py` e `bank.py` girano senza modifiche, e `assemble.py` sostituisce poi la sezione con la nodestring.
* Stampa il numero di sezioni (`B sections N`).

## Parametri e costanti

Nessuna costante: il tag `'B'` e lo stream `'main'` sono fissi nel codice. `tag='B'` è usato poi da `assemble.py` per selezionare le sezioni B.

## Uso

```bash
cp scripts/export_B.py /percorso/WD/work/
```

```bash
python3 /percorso/WD/work/export_B.py /percorso/WD dpB2.pkl
```

Senza il secondo argomento legge `dpB.pkl`, come il 17 novembre.

(layout di `WD`: vedi [dpB.md](dpB.md), sezione Uso.)

## Funzionamento

Per ogni indice `j` di `B` costruisce il record con i valori dei candidati. Se c'è la chiave `anchor`, la aggiunge al record nella posizione `anchor['k']`. Infine scrive la lista in `sec_in.json`.

## Verifiche e limiti

* Il file contiene **solo** le sezioni B: sovrascrive il `sec_in.json` precedente (quello del 2026-11-09 resta nel lavoro originale).
* Il numero di sezioni deve coincidere con `len(B)` (354 sia il 17 sia il 18 novembre, B00000–B17650).
* Non controlla che i valori siano finiti (`tL`, `cL`, … `nan` verrebbero scritti come `NaN`).
