# prep_inputs_nvb.py - second stage (2026-11-17), N/V/B reaches.
# Purpose : prepare the two inputs that dpB.py and the S16130 bank.py run need:
#           1) WD/xn_points.json: every point where a non-section nodestring meets a breakline
#              (used by dpB.py to penalise section toes closer than 5 m to such points);
#           2) WD/s16130/work/sec_in.json: one pseudo-section for bank.py, centred in the right-hand
#              channel crossed by S16130 (future N16050), to find the new right bankpoint.
# Inputs  : WD/in/breaklines_50m.gpkg, WD/in/boundary_50m.gpkg (copies of the layers before the N/V/B update,
#           still containing the old section S16130).
# Outputs : WD/xn_points.json, WD/s16130/work/sec_in.json
# Run     : python3 prep_inputs_nvb.py WD      (Anaconda python: geopandas + shapely)
# Then    : copy bank.py into WD/s16130/work and run  /usr/bin/python3 WD/s16130/work/bank.py WD/s16130
import sys, os, json, warnings
import numpy as np, geopandas as gpd, shapely
from shapely.geometry import LineString
warnings.filterwarnings('ignore')
WD = sys.argv[1]
bl = gpd.read_file(f'{WD}/in/breaklines_50m.gpkg', fid_as_index=True)
bd = gpd.read_file(f'{WD}/in/boundary_50m.gpkg')

# ---- 1) nodestring x breakline points ---------------------------------------------------------
# U = union of all non-empty breaklines; for each nodestring that is not a section (S/V + 5 digits),
# keep the coordinates of its intersection with U (crossing points, or the ends of overlapping parts).
U = shapely.union_all([g for g in bl.geometry if g is not None and not g.is_empty])
pts = []
for n, g in zip(bd.nome, bd.geometry):
    if n[0] in 'SV' and n[1:6].isdigit():
        continue                                   # old sections are not obstacles
    l = LineString(shapely.get_coordinates(g))
    pts += shapely.get_coordinates(l.intersection(U)).tolist()
json.dump(pts, open(f'{WD}/xn_points.json', 'w'))
print('xn points', len(pts))

# ---- 2) pseudo-section for the right-hand channel of S16130 -----------------------------------
# a = left end (sx) of S16130, u = unit vector sx -> dx along the section line.
c = shapely.get_coordinates(bd[bd.nome == 'S16130'].geometry.iloc[0])
a, d = c[0], c[1]
u = (d - a) / np.hypot(*(d - a))
ext = LineString([a, a + u * 60])                  # the section line prolonged 60 m to the right

def t_of(fid):
    # distances along ext (from a) of the crossings with breakline fid, rounded to 1 mm
    return sorted(round(float(np.dot(p - a, u)), 3) for p in shapely.get_coordinates(ext.intersection(bl.geometry[fid])))

# Breaklines met along the line (checked on the map, 2026-11-17):
# 970 = island between the two channels (crossed twice), 853 = right toe of the right channel,
# 1129 = first line of the wall strip inside the urban bank, 949 = top of the urban bank.
toeL = t_of(970)[1]      # right edge of the island = left toe of the right channel (14.717)
toeR = t_of(853)[0]      # right toe of the right channel (20.263)
wall = t_of(1129)[0]     # wall strip (28.133): the search stops 0.5 m before it
top = t_of(949)[0]       # top of bank (41.19)
tm = (toeL + toeR) / 2   # centre of the right channel along the line
o = a + u * tm
tt = toeR - tm           # half width of the right channel = toe distance on both sides
# bank.py convention: +n is the left side, so n = -u makes the R side point towards the right bank.
sec = dict(stream='main', s=16130.0, x=float(o[0]), y=float(o[1]), nx=float(-u[0]), ny=float(-u[1]),
           tL=tt, tR=tt, cL=top - tm, cR=top - tm, maxR=wall - 0.5 - tm)
os.makedirs(f'{WD}/s16130/work', exist_ok=True)
json.dump([sec], open(f'{WD}/s16130/work/sec_in.json', 'w'))
print('S16130 right channel: toeL %.3f toeR %.3f wall %.3f top %.3f' % (toeL, toeR, wall, top), sec)

# ---- 3) breaklines bounding the wall regions (mat_id 11): locked in fix5.py -------------------
# Faces of the planar graph breaklines + non-section nodestrings (no sections); the faces containing a
# region point with mat_id 11 are the walls. Every breakline sharing more than 1 cm with their boundary is listed.
from shapely.ops import polygonize, unary_union
rg = gpd.read_file(f'{WD}/in/regioni_ponti_50m.gpkg', fid_as_index=True)
O = {int(f): shapely.get_coordinates(g) for f, g in bl.geometry.items() if g is not None and not g.is_empty}
NS = [LineString(shapely.get_coordinates(g)) for n, g in zip(bd.nome, bd.geometry) if not (n[0] in 'SV' and n[1:6].isdigit())]
fc = list(polygonize(unary_union([LineString(c) for c in O.values()] + NS)))
T = shapely.STRtree(fc)
walls = {int(T.query(p, predicate='within')[0]) for p in rg[rg.mat_id == 11].geometry}
B = shapely.union_all([fc[i].boundary for i in walls]).buffer(1e-6)
lock = sorted(f for f, c in O.items() if LineString(c).intersection(B).length > 0.01)
json.dump(lock, open(f'{WD}/mat11_lines.json', 'w'))
print('wall faces', len(walls), 'locked breaklines', len(lock), lock)
