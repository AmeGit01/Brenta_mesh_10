# regions2.py - one region point per face of the final planar graph
# Purpose: choose ONE region point per face of the final planar graph (breaklines + nodestrings + sections). Rules: a face holding one of
#          the configured preserved pairs (params.regions2.preserved_pairs) is left as it is; otherwise keep the first point (original
#          points, fid <= originals.region_fid_max, first) that is >= clearance from every line; in narrow faces an original point is
#          never replaced (the one with the largest clearance is kept); otherwise a new point at the pole of inaccessibility (polylabel)
#          with the attributes (name, mat_id, max_area, hole) of the original region the face comes from.
# Inputs : work/near_nodes.json, work/secs_new.json, cfg layers ('out', boundary|regions) = current derived layers, cfg layer ('in','regions')
#          = original region points, work/graph.pkl (graph.py --layers out on the derived layers BEFORE this change: the base faces,
#          used to find the original region of a face), cfg['originals']['region_fid_max'], cfg['rules']['regions']['clearance'],
#          cfg['params']['regions2'].
# Output : work/regions2.json = dict(keep = fids kept, drop = fids to delete, new = new points (face,x,y,name,mat_id,max_area,hole,clear),
#          nfaces); prints counts, dropped/new lists, kept points with clearance < clearance and the status of the report points.
# Run    : cd <WD> ; ~/anaconda3/bin/python3 <toolkit>/scripts/regions2.py [-c rcs_config.json]
# Keep: original point if >= clearance from every line, else the lowest-fid point >= clearance; otherwise a new point
# at the pole of inaccessibility with the attributes of the original region the face comes from.
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common, geom
import json, numpy as np, geopandas as gpd, shapely, warnings, collections; warnings.filterwarnings('ignore')
from shapely.geometry import LineString
from shapely.ops import polygonize, unary_union, polylabel

cfg = common.load(common.parser('one region point per face').parse_args())
P = cfg['params']['regions2']
FMAX = cfg['originals']['region_fid_max']          # fids <= FMAX are original points
CLEAR = cfg['rules']['regions']['clearance']       # minimum distance of a point from every line (m)
PAIRS = [set(p) for p in P['preserved_pairs']]     # faces holding one of these pairs are left as they are
REPORT = P['report_points']                        # region points whose status is printed
TOLP = P['polylabel_tolerance']                    # tolerance of polylabel (m)
fN, fM, fA, fH = (cfg.f('regions', k) for k in ('name', 'mat_id', 'max_area', 'hole'))
# F = new breaklines (>=2 vertices), secs = new sections, bd = boundary
F = {int(k): v for k, v in json.load(open(cfg.work('near_nodes.json')))['F'].items() if len(v) >= 2}
secs = json.load(open(cfg.work('secs_new.json'))); bd = gpd.read_file(cfg.layer('out', 'boundary'), fid_as_index=True)
# NS = non-section nodestrings
NS = [LineString(shapely.get_coordinates(g)) for n, g in zip(bd[cfg.f('boundary', 'name')], bd.geometry) if not cfg.is_section(n)]
# L = all lines; U = their union; fc = faces of the planar graph (polygonize); A = areas
L = [LineString(c) for c in F.values()] + NS + [LineString(s['coords']) for s in secs]
U = unary_union(L); fc = list(polygonize(U)); A = np.array([f.area for f in fc]); print('faces', len(fc), 'area<1 m2', int((A < 1).sum()), sorted(A)[:5])
# r = current region points (out), r0 = original ones (in)
r = geom.read(cfg.layer('out', 'regions')); r0 = geom.read(cfg.layer('in', 'regions'))
# base = faces of graph.pkl (before the edits); b0[face] = original region points (r0) lying in each base face
base, _ = geom.load_graph(cfg); TB = shapely.STRtree(base)
b0 = collections.defaultdict(list)
for p, f in zip(*TB.query(r0.geometry.values, predicate='within')): b0[int(f)].append(int(r0.index[p]))
# rg = region points with a geometry; infc[face] = region points inside each new face
rg = r[r.geometry.notna()]; T = shapely.STRtree(fc); infc = collections.defaultdict(list)
for p, f in zip(*T.query(rg.geometry.values, predicate='within')): infc[int(f)].append(int(rg.index[p]))
# clear[fid] = distance of the region point from the nearest line
clear = dict(zip(rg.index, shapely.distance(U, rg.geometry.values)))
# keep/drop/new = result lists; errs = faces for which no source region was found
keep = []; drop = []; new = []; errs = []
# loop over the faces; ps = points inside, originals first
for i, f in enumerate(fc):
    ps = sorted(infc.get(i, []), key=lambda q: (q > FMAX, q))
    # face with a preserved pair: kept as it is
    pair = next((pr for pr in PAIRS if set(ps) >= pr), None)
    if pair:
        keep += [q for q in ps if q in pair]; drop += [q for q in ps if q not in pair]; continue
    # good = points at >= clearance from every line: keep the first, drop the others
    good = [q for q in ps if clear[q] >= CLEAR]
    if good:
        keep.append(good[0]); drop += [q for q in ps if q != good[0]]; continue
    # narrow face: never replace an original point; keep the one with the largest clearance
    orig_in = [q for q in ps if q <= FMAX]
    if orig_in:
        best = max(orig_in, key=lambda q: clear[q]); keep.append(best); drop += [q for q in ps if q != best]; continue
    # new point at the pole of inaccessibility; c = its clearance; if an existing point is at least as clear, keep that one
    pt = polylabel(f, tolerance=TOLP); c = float(pt.distance(U))
    if ps and max(clear[q] for q in ps) >= c - 1e-6:
        best = max(ps, key=lambda q: clear[q]); keep.append(best); drop += [q for q in ps if q != best]; continue
    # src = region the attributes are copied from: the original region of the base face containing pt, else the first point inside
    src = None
    idx = TB.query(pt, predicate='within')
    if len(idx) and b0.get(int(idx[0])): src = r0.loc[b0[int(idx[0])][0]]
    elif ps: src = r.loc[ps[0]]
    if src is None: errs.append((i, round(A[i], 2))); continue
    # no suitable existing point: drop the ones inside and create the new one
    drop += ps
    new.append(dict(face=i, x=pt.x, y=pt.y, name=src[fN], mat_id=int(src[fM]), max_area=float(src[fA]), hole=None if src[fH] != src[fH] or src[fH] is None else int(src[fH]), clear=c))
# reports
print('kept', len(keep), 'dropped', len(drop), 'new', len(new), 'errors', errs)
print('dropped list', sorted(drop)); print(f'new clearance <{CLEAR:g} m', [(round(p['clear'], 2), p['name']) for p in new if p['clear'] < CLEAR])
print(f'kept with clearance <{CLEAR:g} m', [(q, r.at[q, fN], round(clear[q], 2)) for q in keep if clear[q] < CLEAR])
print('new by name', collections.Counter(p['name'] for p in new))
print('dropped detail', [(q, r.at[q, fN], round(clear[q], 2)) for q in sorted(drop)])
for q in REPORT: print(q, 'kept' if q in keep else ('dropped' if q in drop else 'n/a'), round(clear[q], 2))
# save
json.dump(dict(keep=keep, drop=sorted(drop), new=new, nfaces=len(fc)), open(cfg.work('regions2.json'), 'w'))
