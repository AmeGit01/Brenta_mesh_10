# stats.py

Script esplorativo (non necessario per produrre i layer). Statistiche di larghezza del letto (`B`) e del corridoio letto+sponde (`W`) lungo il percorso principale dello scheletro: km con letto > 30 m / > 20 m, km con corridoio < 40 m, percentili per tratto di easting e per fasce di 3 km. Servito per scegliere la strategia di allargamento. Si usa dopo `net.py` (passo 3).

## Requisiti

`python3` di Anaconda con numpy, shapely, geopandas, scipy (`gaussian_filter1d`). Non importa `core.py`.

## Input

* `WD/work/skel.pkl` (`skel.py`): `vv` (vertici dello scheletro), `bed`, `cor` (poligoni di letto e di corridoio letto+sponde).
* `WD/work/net.pkl` (`net.py`): `paths['main']` (indici dei vertici del percorso principale).

## Output

Solo stampa: `main length <m> sections ~ N`, `km bed>30 ...`, `km bed>20 ...`, `km cor<40 ...`, righe per tratto (`monte`, `tratto report`, `P20-divergenza`, `Borgo`, `a valle Borgo`, `valle`) con percentili 5/50/95 di `cor` e `bed` e frazione `<40`; poi una riga per fascia di 3 km con mediane e easting medio.

## Parametri e costanti

* `1.0` m: ricampionamento; `sigma = 8` campioni (8 m) del filtro gaussiano.
* `700` m: semilunghezza della normale; `10`, `5`: margine iniziale/finale e passo di campionamento (indici, quindi m).
* Intervalli di easting dei tratti (es. 675800-679478, 679780-684663, 684663-687200, 687200-690900, 690900-696000, 696000-705400); fasce di 3 km fino a 33 km; soglie 30, 20, 40 m.

## Uso

```bash
python3 stats.py /percorso/WD
```

## Funzionamento

1. Estrae il percorso principale, lo ricampiona a 1 m e lo liscia.
2. A ogni 5 m intersecca la normale con `cor` e `bed` e prende la lunghezza del tratto che contiene il punto (NaN se manca).
3. Calcola le frazioni e i percentili, stampa.

## Verifiche e limiti

I km sono stimati come frazione di campioni × lunghezza; la selezione per easting suppone un percorso monotono. Solo stampa.
