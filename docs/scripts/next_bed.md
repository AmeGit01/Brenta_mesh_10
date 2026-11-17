# next_bed.py

Se subito oltre la sponda di una sezione c'è il letto di un altro canale (un altro `bed`), limita la distanza massima di ricerca del bankpoint su quel lato, in modo che si fermi 0.5 m prima del bordo di quel letto. È il passo 13 (precedente `export_sec.py`, successivo `bank.py`).

## Requisiti

* Interprete: `python3` di Anaconda.
* Pacchetti: numpy, shapely (tramite `core.py`), `json`.
* Modulo importato: `core.py` (`cls`, `boundary_segs`, `Rays`, `pickle`, `np`, `SP`).

## Input

* `WD/work/newfaces.pkl` (da `place.py`): dict con `fc` (poligoni delle facce dopo l'allargamento) e `rows` (lista di dict con almeno `face`, `nome`).
* `WD/work/sec_in.json` (da `export_sec.py`): usa `x`, `y`, `nx`, `ny`, `tL`, `tR`, `stream`, `s`.

## Output

* `WD/work/sec_in.json`, **sovrascritto sul posto**, con in più i campi `maxL` e/o `maxR` (m, distanza dal centerpoint) nelle sezioni dove scatta il limite. Letto da `bank.py` e `check_bp.py` (che usano `maxL`/`maxR`).
* Stampa una riga ` next-bed cap` per ogni limite (iniziale dello stream, ascissa arrotondata, chiave, valore, distanza del piede) e infine `caps N`.

## Parametri e costanti

* `1500`: lunghezza (m) del raggio per lato.
* `0.05`: m oltre il piede per scartare il bordo del letto proprio.
* `15 + 2`: finestra di ricerca del bankpoint oltre il piede (15 m, come in `bank.py`) più 2 m di margine; l'altro letto conta solo se cade dentro.
* `0.5`: distanza di sicurezza (m) prima dell'altro letto.

Tutte nel corpo del ciclo principale.

## Uso

```bash
python3 next_bed.py /percorso/WD
```

## Funzionamento

1. Costruisce i segmenti di contorno di tutte le facce di classe `bed` (`cls(nome)=='bed'`) e un oggetto `Rays` per le intersezioni raggio-segmenti.
2. Per ogni sezione lancia un raggio dal centerpoint lungo la normale in entrambi i versi (±1500 m) e raccoglie le distanze con segno dei bordi di letto colpiti.
3. Per ciascun lato (sinistro: +, chiave `maxL`, piede `tL`; destro: −, chiave `maxR`, piede `tR`) prende le distanze oltre il piede (+0.05 m), ordinate.
4. Se la prima cade entro `piede + 15 + 2` (con 0.5 m tolto), imposta `s[maxX] = d - 0.5` solo se più piccolo di un eventuale valore già presente.

## Verifiche e limiti

* Idempotente (un limite viene solo abbassato), ma sovrascrive `sec_in.json` senza backup; se si riesegue `export_sec.py` va rieseguito anche questo.
* Controllare le righe `next-bed cap` stampate: ci si aspetta pochi casi, localizzati dove due letti sono vicini (Brenta vecchio, Borgo, diramazioni).
* Considera il bordo di qualsiasi faccia `bed`, inclusi i letti non collegati al canale principale.
* Il limite è una distanza lungo la normale dal centerpoint; in `bank.py` viene applicato anche alla finestra di ricerca come `cap5 = min(cc-5, maxX)`.
