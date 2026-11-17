# dp.py

Step 11. Programmazione dinamica sui candidati ogni 0.25 m di `place.py` per scegliere le stazioni delle sezioni: prima sezione a `s` in [49.5, 50.5] m, poi stazioni successive a 49.5-50.5 m di distanza (corda tra i punti), con penalità per i vincoli violati. Il Brenta vecchio viene risolto dopo l'asta ed è penalizzato dove le sue sezioni incrocerebbero quelle dell'asta. Segue `place.py`, precede `export_sec.py`.

## Requisiti

* Python di Anaconda: numpy, shapely.
* Importa `core.py` (`pickle`, `np`, `shapely`, `SP`).

## Input

* `WD/work/cands.pkl` (`place.py`): per `main` e `vecchio`: `ss`, `P`, `n`, `tL`, `tR`, `cL`, `cR`, `pen5`, `hitB`, `hitO`, `ok`.

## Output

* `WD/work/dp.pkl`: dict `{'main': array int, 'vecchio': array int}`, indici dei candidati scelti in `cands[name]` (la progressiva è `ss[indice] = 0.25·indice`). Letto da `export_sec.py`.
* stdout, per ciascuna centerline: numero di sezioni, primo e ultimo `s`, lunghezza e costo, minimo/massimo della corda e numero di violazioni (con `s` e valori), conteggio di `hitB`, `hitO`, `pen5` sulle sezioni scelte, minimo/massimo di `ds` e frazione di passi esattamente 50 m; per il vecchio anche quanti candidati incrociano sezioni dell'asta e fino a quale `s` il vecchio è raggiungibile.

## Parametri e costanti

* Penalità per candidato: `pen5 + 1000·hitO + 10000·hitB (+ extra)`; candidato non valido (`ok=False`): 1e9.
* Partenza: `s` in [49.5, 50.5] con costo `0.01·(s-50)²`.
* Passi ammessi `D = [198..202]` indici (49.5-50.5 m di `ss`).
* Costo di transizione: `pen[j] + 0.01·(d·0.25-50)² + (0 se corda in [49.5, 50.5] altrimenti 500 + 100·|corda-50|)`.
* Fine dell'asta: tra i candidati con `s` in [`L-50.5`, `L-5`] (con `L = ss[-1]+0.25`) quello di costo minimo.
* Estensione approssimata delle sezioni per l'incrocio vecchio/asta: `min(t+15, c-5)` per lato; penalità `1e5` per incrocio.
* Vecchio: raggiungibile = costo finito e < 1e4; fine = candidato di costo minimo entro 0.75 m dall'ultimo raggiungibile.

## Uso

```bash
python3 dp.py /percorso/WD
```

## Funzionamento

1. `dp(c, name, extra)`: costo minimo `cost[j]` e predecessore `prev[j]` per ogni candidato, con passaggio in avanti da ogni partenza valida su 5 possibili passi; `name` non è usato.
2. `walk(prev, j)`: ricostruisce la catena all'indietro.
3. Asta: sceglie l'ultimo candidato e ricostruisce; stampa le verifiche.
4. Costruisce le sezioni approssimate dell'asta come ostacoli (`STRtree`) e marca con `1e5` i candidati del vecchio che le intersecano.
5. Vecchio: stesso DP con quella penalità aggiuntiva; sceglie il punto raggiungibile più avanzato e ricostruisce.
6. Salva `dp.pkl`.

## Verifiche e limiti

* Atteso: 0 violazioni di corda (`viol 0`), `hitB 0`, `hitO 0`, `pen5 0`; valori > 0 indicano vincoli non rispettabili in quel tratto.
* Il passo in `ss` è 49.5-50.5 m, ma il vincolo effettivo è sulla corda tra punti: la distanza lungo la linea può differire leggermente.
* Il costo è quadratico ma molto piccolo (0.01) rispetto alle penalità: preferisce comunque stazioni vicine a 50 m esatti.
* Il vecchio può non essere coperto fino alla fine se non esiste catena ammissibile: controllare "reachable to s" rispetto a `L`.
* La fine del vecchio è scelta diversamente dall'asta: vicino al candidato raggiungibile più avanzato, non nell'intervallo [L-50.5, L-5].
