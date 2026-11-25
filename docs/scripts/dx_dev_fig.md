# dx_dev_fig.py

Quarto passo (2026-11-19). Disegna le figure dell'analisi del passo tra le sezioni, [Brenta_analisi_passo_50m.md](../Brenta_analisi_passo_50m.md). Non legge i layer e non scrive nulla fuori dalla cartella delle figure.

## Requisiti

* Interprete: `python3` di Anaconda (pandas, numpy, matplotlib, shapely).

## Input

* Argomento 1: il CSV delle coppie scritto da `dx_dev.py`, normalmente `docs/Brenta_dx_dev_50m.csv`. Servono le colonne `sez_monte`, `sez_valle`, `ramo`, `dx_c`, `dx_avg`, `diff_avg_c`, `dx_dev`, `ang_gradi`, `larg_m` ed `eccezione`.
* Argomento 2: la cartella delle figure, normalmente `docs/figures` (creata se manca).

## Output

Otto PNG a 150 dpi:

| File | Contenuto |
|---|---|
| `fig01_schema_dx.png` | schema delle grandezze: (a) una coppia di sezioni con dx_c, dx_avg, dx_min, dx_max e dx_dev; (b) un tratto in curva con la serie dei dx_avg,i, la media, il minimo e dx_dev_abs |
| `fig02_dx_avg_rami.png` | dx_avg di ogni coppia lungo i rami (presi dalla colonna `ramo` del CSV), con la media del ramo |
| `fig03_diff_avg_c_rami.png` | dx_avg − dx_c lungo i rami |
| `fig04_diff_avg_c_angolo.png` | dx_avg − dx_c in funzione dell'angolo tra le sezioni |
| `fig05_dx_dev_istogramma.png` | istogramma di dx_dev per ramo, con le eccezioni in grigio e la mediana |
| `fig06_dx_dev_geometria.png` | dx_dev in funzione di larghezza · tan(angolo) / dx_avg, con la correlazione |
| `fig07_dx_avg_ordinati.png` | dx_avg in ordine crescente, con la media dell'intero modello |
| `fig08_sensibilita.png` | dx_dev_abs dell'intero modello togliendo le k coppie più corte, k = 0…20, con tutte le coppie e senza eccezioni |

## Uso

```bash
~/anaconda3/bin/python3 scripts/dx_dev_fig.py docs/Brenta_dx_dev_50m.csv docs/figures
```

Va lanciato dopo `dx_dev.py`, dalla cartella del progetto.

## Funzionamento

* **Progressiva.** Nelle figure 2 e 3 l'asse orizzontale è la progressiva nominale del punto medio della coppia, ricavata dal nome delle sezioni (indice × 50 m), in km.
* **Colori.** Un colore per ramo (N blu, V arancione, B verde), sempre lo stesso in tutte le figure. Le coppie con `eccezione` = 1 sono cerchi vuoti grigi.
* **Etichette.** Le figure 2 e 3 indicano le coppie più lontane dalla media del ramo (o da zero); le etichette di punti vicini sono sfalsate.
* **Schema della figura 1.** La geometria è inventata: in (a) due sezioni di 32 m inclinate di 28°; in (b) un rettilineo, una curva di raggio 60 m e di 75°, e sezioni di 34 m normali alla linea d'asse ogni 50 m. Le distanze sono calcolate con lo stesso campionamento di `dx_dev.py` (201 punti per sezione), quindi i numeri scritti nella figura sono coerenti con le definizioni.
* **Sensibilità.** dx_dev_abs = (media − min) / media, ricalcolato sulla serie ordinata dei dx_avg dopo aver tolto i primi k valori.

## Verifiche

* I valori della figura 8 per k = 0, 1, 2, 3, 5 e 10 coincidono con la tabella di sensibilità stampata da `dx_dev.py`.
* La correlazione scritta nella figura 6 (0.96) coincide con quella stampata da `dx_dev.py`.

## Limiti

* Le figure sono statiche: per leggere i valori di una coppia si usa il CSV.
* La progressiva nominale non è la progressiva vera della linea d'asse: nel ramo B le sezioni partono dalla B00000 e i nomi seguono l'indice, non i metri.
