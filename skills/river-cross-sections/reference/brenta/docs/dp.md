# dp.py

Step 11. Dynamic programming over the candidates every 0.25 m of `place.py`, to choose the stations of the sections: first section at `s` in [49.5, 50.5] m, then following stations at 49.5-50.5 m apart (chord between the points), with penalties for the violated constraints. The Brenta vecchio is solved after the main reach and is penalized where its sections would cross those of the main reach. It follows `place.py` and precedes `export_sec.py`.

## Requirements

* Anaconda Python: numpy, shapely.
* Imports `core.py` (`pickle`, `np`, `shapely`, `SP`).

## Input

* `WD/work/cands.pkl` (`place.py`): for `main` and `vecchio`: `ss`, `P`, `n`, `tL`, `tR`, `cL`, `cR`, `pen5`, `hitB`, `hitO`, `ok`.

## Output

* `WD/work/dp.pkl`: dict `{'main': int array, 'vecchio': int array}`, indices of the candidates chosen in `cands[name]` (the chainage is `ss[index] = 0.25·index`). Read by `export_sec.py`.
* stdout, for each centerline: number of sections, first and last `s`, length and cost, minimum/maximum of the chord and number of violations (with `s` and values), count of `hitB`, `hitO`, `pen5` on the chosen sections, minimum/maximum of `ds` and the fraction of steps exactly 50 m; for the vecchio also how many candidates cross sections of the main reach and up to which `s` the vecchio is reachable.

## Parameters and constants

* Penalty per candidate: `pen5 + 1000·hitO + 10000·hitB (+ extra)`; invalid candidate (`ok=False`): 1e9.
* Start: `s` in [49.5, 50.5] with cost `0.01·(s-50)²`.
* Admitted steps `D = [198..202]` indices (49.5-50.5 m of `ss`).
* Transition cost: `pen[j] + 0.01·(d·0.25-50)² + (0 if chord in [49.5, 50.5] otherwise 500 + 100·|chord-50|)`.
* End of the main reach: among the candidates with `s` in [`L-50.5`, `L-5`] (with `L = ss[-1]+0.25`), the one of minimum cost.
* Approximate extent of the sections for the vecchio/main crossing: `min(t+15, c-5)` per side; penalty `1e5` per crossing.
* Vecchio: reachable = finite cost and < 1e4; end = candidate of minimum cost within 0.75 m of the last reachable one.

## Usage

```bash
python3 dp.py /path/to/WD
```

## How it works

1. `dp(c, name, extra)`: minimum cost `cost[j]` and predecessor `prev[j]` for each candidate, with a forward pass from each valid start over 5 possible steps; `name` is not used.
2. `walk(prev, j)`: rebuilds the chain backwards.
3. Main reach: chooses the last candidate and rebuilds; prints the checks.
4. Builds the approximate sections of the main reach as obstacles (`STRtree`) and marks with `1e5` the candidates of the vecchio that intersect them.
5. Vecchio: same DP with that extra penalty; chooses the most advanced reachable point and rebuilds.
6. Saves `dp.pkl`.

## Checks and limits

* Expected: 0 chord violations (`viol 0`), `hitB 0`, `hitO 0`, `pen5 0`; values > 0 indicate constraints that cannot be respected in that stretch.
* The step in `ss` is 49.5-50.5 m, but the effective constraint is on the chord between points: the distance along the line may differ slightly.
* The cost is quadratic but very small (0.01) compared with the penalties: it still prefers stations close to exactly 50 m.
* The vecchio may not be covered up to the end if no admissible chain exists: check "reachable to s" against `L`.
* The end of the vecchio is chosen differently from the main reach: near the most advanced reachable candidate, not in the interval [L-50.5, L-5].
