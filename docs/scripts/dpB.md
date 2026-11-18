# dpB.py

Secondo passo (2026-11-17), primo script. Ricolloca il tratto **B** (Brenta a valle di Borgo) sui candidati dell'asta principale (`cands.pkl`) con la programmazione dinamica, rispettando i vincoli sul ponte Bordignon e la regola dei 5 m. Sostituisce per il solo ramo B il lavoro di `dp.py`. Precedente: `place.py`/`dp.py`; successivo: `export_B.py`.

## Requisiti

* Interprete: `python3` di Anaconda (numpy, scipy `cKDTree`, shapely tramite `core.py`).
* Modulo importato: `core.py` da `WD/work` (fornisce `SP` = `sys.argv[1]`, `pickle`, `np`).
* Lo script va copiato in `WD/work` (dove si trovano anche `core.py`, `cands.pkl`, `dp.pkl`).

## Input

* `WD/work/cands.pkl` (`place.py`): candidati; usa la chiave `main` con `ss` (progressiva sull'asta, passo 0.25 m), `P` (centerpoint), `n` (normale), `tL`, `tR` (distanze del piede), `ok`, `pen5`, `hitO`, `hitB`.
* `WD/work/dp.pkl` (`dp.py`): indici scelti il 2026-11-09 per `main` e `vecchio`.
* `WD/xn_points.json` (nella radice di `WD`, non in `work/`): lista di punti `[x, y]` dove una nodestring non-sezione incontra una breakline. **Nessuno script della pipeline lo produce**: è stato preparato a parte.

## Output

* `WD/work/dpB.pkl`: dizionario con `N` (indici dell'asta mantenuti, quelli con `s <= 16130.5`), `B` (nuovi indici del ramo B), `V` (primi 60 indici del Brenta vecchio da `dp.pkl`).
* Stampa: numero, prime e ultima progressiva di B, costo; intervallo dei passi e delle corde; eventuali corde fuori da 49.5–50.5 m; numero di `hitB`/`hitO`, somma di `pen5`, numero di candidati con penalità ≥ 1e9.

## Parametri e costanti

* `S_BRIDGE = 16327.97` m: progressiva (vecchia) di `Ponte_Bordignon_monte`.
* `MARGIN = 5.0` m: B00050 deve stare almeno 5 m a monte del ponte; i candidati in `(S_BRIDGE − MARGIN, S_BRIDGE + 20)` sono vietati (penalità 1e9).
* `S0MIN = 16266.0`, `S0MAX = 16285.0` m: finestra in cui cade la prima sezione (B00000) sulla vecchia progressiva. L'ultima esecuzione ha usato `S0MIN=16266`.
* Penalità: `pen5` + 1000·`hitO` + 10000·`hitB`; candidati non `ok`: 1e9; +50 per ogni lato il cui incrocio con il piede cade a meno di 5 m da un punto di `xn_points.json`.
* Passi ammessi: `d ∈ {198..202}` celle da 0.25 m (49.5–50.5 m di progressiva); costo del passo `0.01·(d·0.25 − 50)²`; corda fuori da 49.5–50.5 m: +500 + 100·|corda − 50|.
* Fine: ultima sezione a 5–50.5 m prima della fine della progressiva (`L = ss[-1] + 0.25`).
* `16130.5` m: limite superiore degli indici `N` mantenuti.

## Uso

Layout della cartella di lavoro (`WD`, es. `.../v2`): `WD/in` (copie dei sei `layers/*_50m.gpkg`), `WD/in0` (copie degli originali `breaklines.gpkg`, `boundary.gpkg`, `regioni_ponti.gpkg`), `WD/work` (`core.py`, `next_bed.py`, `bank.py` e `cands.pkl`, `newfaces.pkl`, `dp.pkl`, `cltab.pkl` del lavoro del 2026-11-09), `WD/s16130/work` (esecuzione di `bank.py` per l'estensione di S16130), `WD/xn_points.json`.

```bash
cp scripts/dpB.py /percorso/WD/work/
```

```bash
python3 /percorso/WD/work/dpB.py /percorso/WD
```

## Funzionamento

1. Carica i candidati `main` e costruisce il vettore di penalità `pen` (vedi sopra); i punti del piede di ogni candidato (`P ± n·t`) sono confrontati con i punti `xn_points.json` tramite un KD-tree.
2. Annulla (1e9) i candidati nella zona del ponte.
3. Programmazione dinamica in avanti: `cost` parte da `pen` per i candidati con `ss ∈ [S0MIN, S0MAX]`; da ogni candidato `i` con costo < 1e9 si passa a `j = i + d`, aggiornando costo e predecessore.
4. Sceglie la fine di costo minimo nella finestra `[L − 50.5, L − 5]`, risale i predecessori e stampa le verifiche.
5. Salva `N` (indici di `dp.pkl['main']` con `ss <= 16130.5`), `B` e `V`.

## Verifiche e limiti

* Controllare nella stampa: corde tutte in 49.5–50.5 m (lista vuota), `hitB`/`hitO` = 0, `pen>=1e9` = 0.
* `xn_points.json` non è generato da nessuno script: va fornito (se manca, lo script si ferma con `FileNotFoundError`).
* Le costanti sono nel codice; l'indice di `S0MIN` è stato scelto a mano (16266).
* Sovrascrive `dpB.pkl` a ogni esecuzione.
