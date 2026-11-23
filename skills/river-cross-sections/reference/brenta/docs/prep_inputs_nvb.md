# prep_inputs_nvb.py

Prepares the two input files of the second pass (17 November 2026, reaches N/V/B) that are not produced by other scripts:

* `WD/xn_points.json`: the points where a nodestring that is not a section meets a breakline. `dpB.py` uses them to penalize the B reach sections whose toe falls less than 5 m from one of these points;
* `WD/s16130/work/sec_in.json`: a dummy section centred in the right channel crossed by S16130 (the future N16050). It is used by `bank.py` to look for the new right bankpoint when the section is extended to that channel.

It also produces `WD/mat11_lines.json`: the list of breaklines that bound the wall strips (regions with `mat_id` 11). `fix5.py` must leave them exactly as they are.

It must be run first, before `dpB.py`. The next step that uses the second file is the run of `bank.py` in the `s16130/` folder.

## Requirements

* Anaconda Python (`python3`) with geopandas, shapely and numpy.
* No other project script.

## Input

* `WD/in/breaklines_50m.gpkg`: copy of the breaklines before the N/V/B update. The lines 970, 853, 1129 and 949 around S16130 are needed.
* `WD/in/boundary_50m.gpkg`: copy of the nodestrings before the update, which still contains the old section `S16130`. The old sections are recognized by name: `S` or `V` followed by five digits.

## Output

* `WD/xn_points.json`: list of pairs `[x, y]`. These are the intersections of each nodestring that is not a section with the union of the breaklines, including the ends of the stretches where the two lines overlap. On 17 November there were 197 points.
* `WD/s16130/work/sec_in.json`: list with a single element, in the format of `bank.py`. The fields are `stream`, `s`, `x`, `y` (centre of the right channel), `nx`, `ny` (normal pointing to the left, so the R side looks towards the right bank), `tL`, `tR`, `cL`, `cR` and `maxR`. `tL` and `tR` are the half-width of the channel. `cL` and `cR` are the distance from the top of bank, i.e. the line 949. `maxR` is the search limit, 0.5 m before the wall strip 1129.

* `WD/mat11_lines.json`: list of the fids of the breaklines that share more than 1 cm with the outline of a wall face. On 17 November there were 32: 893, 910–913, 915, 916, 918, 972, 1062, 1063, 1068–1071, 1125–1133 and 1135–1142.

The list of locked lines also needs `WD/in/regioni_ponti_50m.gpkg`, to find the points with `mat_id` 11.

## Parameters and constants

| Constant | Value | Meaning |
|---|---|---|
| section | `S16130` | section to extend, searched by name in `boundary_50m` |
| extension | 60 m | length of the section line towards the right on which the crossings are searched |
| 970 | 2nd crossing (14.717 m) | right edge of the island between the two channels, i.e. the left toe of the right channel |
| 853 | 20.263 m | right toe of the right channel |
| 1129 | 28.133 m | first line of the wall strip inside the urban bank |
| 949 | 41.19 m | top of the urban bank |
| margin | 0.5 m | minimum distance from the obstacle (bankpoint rule) |

The distances are measured along the section line starting from its left end and rounded to the millimetre, as in the original calculation. The breakline numbers are fixed in the code: they are valid only for this section and for this data.

## Usage

Prepare the working folder with the copies of the layers:

```bash
mkdir -p WD/in
```

```bash
cp layers/breaklines_50m.gpkg layers/boundary_50m.gpkg WD/in/
```

Run the script:

```bash
python3 scripts/prep_inputs_nvb.py WD
```

Then compute the right bankpoint of the extended S16130:

```bash
cp scripts/bank.py WD/s16130/work/
```

```bash
/usr/bin/python3 WD/s16130/work/bank.py WD/s16130
```

## How it works

1. Merges all the non-empty breaklines into a single geometry.
2. For each nodestring that is not a section, computes its intersection with that union and saves the coordinates in `xn_points.json`.
3. Takes the old S16130 and extends it by 60 m to the right, starting from its left end.
4. Along this line measures where it crosses the lines 970, 853, 1129 and 949.
5. Builds a dummy section centred in the right channel, with toes, top and search limit taken from those crossings. `bank.py` will look for the bankpoint from the right toe outwards and stop 0.5 m before the wall.
6. Rebuilds the planar graph of breaklines and nodestrings, without sections, and finds the faces that contain a region point with `mat_id` 11, i.e. the wall strips (19 faces). Saves the fids of the breaklines that form their outline, even for a stretch longer than 1 cm.

## Checks and limits

* On 17 November the two files produced were identical to those used for the work.
* The script works only on the layers **before** the N/V/B update. After the update `S16130` no longer exists (it is called `N16050`) and the breaklines have been modified.
* The line identifiers (970, 853, 1129, 949) were chosen by looking at the map. If the data change, they must be checked again.
* With the new sections (`N`, `V`, `B`) the name filter would not recognize them as sections: it applies only to the old names `S` and `V`.
