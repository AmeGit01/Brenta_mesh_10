# gaps.py

Step 9. **Print-only** connectivity check: it finds the line ends that in the original data touched another breakline (within 1 mm) but, after the widening, touch nothing. It follows `apply_widen.py` and precedes `place.py`. It writes no files.

## Requirements

* Anaconda Python: shapely, numpy.
* Imports `core.py` (`pickle`, `shapely`, `LineString`, `Point`, `SP`).

## Input

* `WD/work/chains.pkl` (`chains.py`): `feat` (fid -> original vertices).
* `WD/work/widen2.pkl` (`apply_widen.py`): `newf` (fid -> new vertices of the changed features); `endmap` is read but not used.

## Output

Only stdout: first the number of "broken" ends, then up to 60 tuples `(fid, end, new xy, nearby original fids (max 4), original xy)`, where end is `0` (first vertex) or `-1` (last). Expected: `0`. If > 0, the listed ends must be inspected or corrected.

## Parameters and constants

* Contact tolerance `1e-3` m (line 10).
* List limited to 60 rows (line 18).

## Usage

```bash
python3 gaps.py /path/to/WD
```

## How it works

1. Builds two sets of `LineString`: the originals (`old`) and the widened ones (`new`, with `newf` in place of the originals), each with its `STRtree`.
2. For each feature and for each of its two ends, looks for the other lines within 1 mm in the original set and in the new one.
3. If there was at least one neighbour in the original and none in the new one, records the end.

## Checks and limits

* The lines of `boundary.gpkg` (nodestrings) are not considered, neither in the original nor in the new set.
* Only contacts at the ends are considered (an end that touched before and now touches a different line passes the check).
* The check covers "end-on-line" contacts within 1 mm; it does not verify planarity or the absence of overlaps.
