# graph.py - planar graph of breaklines + boundary lines, its faces and their region points (face classes by region name)
# Purpose: build the planar graph of the breaklines and boundary lines (lines are noded exactly with unary_union, faces made by
#          polygonize), assign to each face the region point that lies inside it, print diagnostics. work/graph.pkl is the base of
#          next_bed.py, obst.py and regions2.py (and of any step that needs the faces and their classes).
# Inputs : cfg layers of group 'in' (default: the original breaklines, boundary, regions) or of group 'out' (--layers out: the
#          derived layers, e.g. to get the faces of the current model). Fields: cfg.f('regions','name'), cfg.f('regions','mat_id').
# Outputs: work/graph.pkl = dict(faces, fr, rows); diagnostics on stdout (see the sheet docs/scripts/graph.md).
# Run    : cd <WD> ; ~/anaconda3/bin/python3 <toolkit>/scripts/graph.py [-c rcs_config.json] [--layers in|out]
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common
import geopandas as gpd, numpy as np, shapely, pickle, collections
from shapely.ops import polygonize, unary_union
from shapely.geometry import LineString

ap = common.parser('planar graph of breaklines + boundary and its faces')
ap.add_argument('--layers', choices=['in', 'out'], default='in', help="layer group to use: 'in' = original layers (default), 'out' = derived layers")
args = ap.parse_args()
cfg = common.load(args)
W = args.layers
fN, fM = cfg.f('regions', 'name'), cfg.f('regions', 'mat_id')
# b = breaklines, bd = boundary lines, r = region points (fid_as_index keeps the GPKG fid as the DataFrame index)
b = gpd.read_file(cfg.layer(W, 'breaklines'), fid_as_index=True); bd = gpd.read_file(cfg.layer(W, 'boundary'), fid_as_index=True); r = gpd.read_file(cfg.layer(W, 'regions'), fid_as_index=True)
# diagnostic: number of breaklines, empty/null geometries, histogram of number of parts per geometry
print('bl', len(b), 'empty', int((b.geometry.is_empty | b.geometry.isna()).sum()), 'parts', b.geometry.dropna().apply(lambda g: len(g.geoms) if g.geom_type.startswith('Multi') else 1).value_counts().to_dict())
# drop empty/null breaklines
b = b[~(b.geometry.is_empty | b.geometry.isna())]
# lines(s): explode every (multi)geometry of GeoSeries s into plain 2D LineStrings (drops Z/M)
def lines(s):
    out = []
    for g in s.geometry:
        out += [LineString(np.asarray(shapely.get_coordinates(p))) for p in shapely.get_parts(g)]
    return out
# all breaklines + boundary lines; unary_union nodes the lines at their intersections; polygonize builds the faces they enclose
L = lines(b) + lines(bd)
u = unary_union(L)
faces = list(polygonize(u))
print('exact', 'faces', len(faces))
# A = face areas (m2); prints number of faces with area <1e-3 m2 and <1 m2, and total area in km2
A = np.array([f.area for f in faces]); print('area small', (A < 1e-3).sum(), (A < 1).sum(), A.sum() / 1e6)
# spatial index of the faces; assign each region point to the face that contains it
t = shapely.STRtree(faces)
ix = t.query(r.geometry.values, predicate='within')
# ix[0] = point index, ix[1] = face index; check how many region points fall inside a face
print('points in faces', len(set(ix[0])), 'of', len(r))
# pts = number of region points per face; prints how many faces have 0,1,2.. points
pts = np.bincount(ix[1], minlength=len(faces)); print('faces per npoints', np.unique(pts, return_counts=True))
# faces larger than 1 m2 with no region point (face index, area), 15 largest printed
big0 = [(i, A[i]) for i in np.where(pts == 0)[0] if A[i] > 1]
print('faces>1m2 w/o point', len(big0), sorted(big0, key=lambda x: -x[1])[:15])
# fid of region points lying in no face
pts_out = [int(f) for k, f in enumerate(r.index) if k not in set(ix[0])]; print('pts outside', pts_out)
# fr: face index -> list of region-point positions inside it
fr = {}
for p, f in zip(*ix):
    fr.setdefault(int(f), []).append(int(p))
# cols: region table with fid as a column; rows: one dict per face that has a point: fid list of its points, name and mat_id of the FIRST point, area (m2)
cols = r.reset_index()
rows = []
for f, ps in fr.items():
    rows.append(dict(face=f, fid=[int(cols.fid[p]) for p in ps], nome=cols[fN][ps[0]], mat=int(cols[fM][ps[0]]), area=A[f]))
# write graph.pkl: faces (list of Polygons), fr (face -> point positions), rows
pickle.dump(dict(faces=faces, fr=fr, rows=rows), open(cfg.work('graph.pkl'), 'wb'))
# summary: for each region name, number of faces and total area in hectares (sorted by area, descending)
agg = collections.defaultdict(lambda: [0, 0.0])
for x in rows:
    agg[x['nome']][0] += 1; agg[x['nome']][1] += x['area']
for k, v in sorted(agg.items(), key=lambda kv: -kv[1][1]): print(f'{k:35s} {v[0]:4d} {v[1]/1e4:10.1f} ha')
# face classes (cfg.face_class) of the faces that have a region point
cc = collections.Counter(cfg.face_class(x['nome']) for x in rows); print('face classes', dict(cc))
