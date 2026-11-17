# bq.py

Script esplorativo (non necessario per produrre i layer). Riassume i risultati del calcolo dei bankpoint per tratto dell'asta: conteggio dei tipi, larghezze mediane e distanza bankpoint-ciglio. Si usa dopo `bank.py` (passo 14), a mano.

## Requisiti

`python3` di Anaconda, numpy; stdlib `json`, `collections`. Non importa `core.py`.

## Input

* `WD/work/sec_in.json` (`export_sec.py`/`next_bed.py`): `stream`, `s`, `cL`, `cR`, `tL`, `tR`.
* `WD/work/bank_out.json` (`bank.py`): per lato `kind`, `t`, `limit`, `z`, `ztoe`, `zrange`.

## Output

Solo stampa. Per ogni tratto: `stream a-b n=<sezioni> {kind: conteggio} W med B med t_to_top min/med`, dove W = `cL + cR` (larghezza ciglio-ciglio), B = `tL + tR` (larghezza del letto), `t_to_top` = distanza ciglio − bankpoint (m) per tutti i lati. Poi fino a 14 righe ` sample` di bankpoint `fallback` nel tratto 4200-10200 m con piede, limite, ciglio, `t`, `z`, `ztoe`, `zmax`.

## Parametri e costanti

* Tratti dell'asta (ascissa m): 0-4200, 4200-10200, 10200-13200, 13200-17400, 17400-22800, 22800-34100; e vecchio 0-4000.
* `14`: numero massimo di campioni `fallback`; tratto di riferimento 4200-10200.

## Uso

```bash
python3 bq.py /percorso/WD
```

## Funzionamento

Unisce sezioni e bankpoint per posizione, filtra per stream e intervallo di `s`, e calcola Counter dei `kind`, mediane di W e B e minimo/mediana della distanza ciglio-bankpoint; infine stampa i campioni `fallback`.

## Verifiche e limiti

Solo lettura e stampa; i tratti sono scelti a mano per l'analisi del 2026-11-09. Se `sec_in.json` e `bank_out.json` non hanno lo stesso numero/ordine di elementi, `zip` tronca senza avvisi. I campioni `fallback` accedono a `ztoe`, presente per i bankpoint di tipo `fallback`.
