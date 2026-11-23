# chains.py - classify every segment of every breakline by the face classes on its two sides; find the top-of-bank lines
# Purpose: find which breaklines are 'top of bank' lines that widen.py may move: a segment is a top segment when it separates the bank
#          class from one of the neighbour classes (the other editable classes and the default class of cfg face_classes).
# Inputs : work/graph.pkl (graph.py); original breaklines layer; config: face_classes.{order,classes,default,fixed,editable},
#          widening.{enabled,bank_class,never_move}; fields.regions.name is not needed (graph.pkl carries the names).
# Outputs: work/chains.pkl = dict(feat, S, meta, L, R, Lc, Rc, istop) read by widen.py, apply_widen.py, gaps.py and the placement step;
#          diagnostics on stdout. L/R = region names left/right of each segment; Lc/Rc = face CLASS names (config names).
# Run    : cd <WD> ; ~/anaconda3/bin/python3 <toolkit>/scripts/chains.py [-c rcs_config.json]
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common, geom
import pickle, collections, numpy as np, shapely, geopandas as gpd

args = common.parser('classify breakline segments by the face classes on both sides (top-of-bank detection)').parse_args()
cfg = common.load(args)
WZ = cfg.get('widening')
if not WZ:
    raise SystemExit("config error: section 'widening' is missing (see config_fragments/widen.json)")
if not WZ.get('enabled', False):
    print('widening.enabled is false: nothing to do'); sys.exit(0)
FC = cfg['face_classes']
for k in ('fixed', 'editable'):
    if k not in FC:
        raise SystemExit(f"config error: face_classes.{k} is missing (list of class names; fixed = outline must not change, editable = outline may move)")
if 'bank_class' not in WZ:
    raise SystemExit("config error: widening.bank_class is missing (the face class whose outer line is the top of bank)")
BANK = WZ['bank_class']
# neighbour classes of the bank across which a segment counts as top of bank: the other editable classes and the default class
NEIGH = [c for c in FC['editable'] if c != BANK] + [FC['default']]
NEVER = set(WZ.get('never_move', FC.get('fixed_bank_names', [])))

# faces and rows (faces with a region point) from graph.pkl
faces, rows = geom.load_graph(cfg)
# fname: face index -> region name
fname = {r['face']: r['nome'] for r in rows}
# tree = spatial index of the faces (for point-in-face tests)
tree = shapely.STRtree(faces)
# breaklines (fid = GPKG feature id), empty geometries removed
bl = gpd.read_file(cfg.layer('in', 'breaklines'), fid_as_index=True); bl = bl[~(bl.geometry.is_empty | bl.geometry.isna())]
# feat: fid -> vertex array (first part only); segs/meta: all non-degenerate segments (>1e-6 m) as [x0,y0,x1,y1] with (fid, segment index)
feat = {}; segs = []; meta = []
for fid, g in bl.geometry.items():
    a = shapely.get_coordinates(next(iter(shapely.get_parts(g))))
    feat[fid] = a
    for i in range(len(a) - 1):
        if np.hypot(*(a[i + 1] - a[i])) > 1e-6: segs.append(np.r_[a[i], a[i + 1]]); meta.append((fid, i))
# S = segments (N,4)
S = np.array(segs)
# d = segment vector; n = unit LEFT normal of each segment (relative to the vertex order of the line); mid = midpoints
d = S[:, 2:] - S[:, :2]; n = np.c_[-d[:, 1], d[:, 0]] / np.hypot(*d.T)[:, None]
mid = (S[:, :2] + S[:, 2:]) / 2
# loc(pts): name of the face containing each point; 'outside' if in no face, 'noname' if the face has no region point
def loc(pts):
    idx = tree.query(shapely.points(pts), predicate='within'); out = np.array(['outside'] * len(pts), dtype=object)
    for p, f in zip(*idx): out[p] = fname.get(int(f), 'noname')
    return out
# L / R = name of the face 2 cm to the left / right of each segment (midpoint +-0.02 m * normal)
L = loc(mid + n * 0.02); R = loc(mid - n * 0.02)
# Lc/Rc = class of left/right face (or 'outside'/'noname')
cl = lambda a: np.array([cfg.face_class(x) if x not in ('outside', 'noname') else x for x in a], dtype=object)
Lc, Rc = cl(L), cl(R)
# histogram of (class,class) pairs across segments, most common first
T = collections.Counter(tuple(sorted((a, b))) for a, b in zip(Lc, Rc)); print(T.most_common())
# istop[k] = True when the segment separates a bank face from a neighbour class: it is a top-of-bank line
pairs = [{BANK, c} for c in NEIGH]
istop = np.array([{a, b} in pairs for a, b in zip(Lc, Rc)])
# tm: fid -> list of istop flags of its segments
tm = {}
for (fid, i), t in zip(meta, istop): tm.setdefault(fid, []).append(t)
# features entirely made of top segments / only partly (mixed); widen.py skips the mixed ones
print('feat all top', sum(all(v) for v in tm.values()), 'some', sum(any(v) and not all(v) for v in tm.values()))
print('mixed feats sample', [k for k, v in tm.items() if any(v) and not all(v)][:20])
# features touching a never-move face (by region name or by class): widen.py does not move them
never = [fid for (fid, i), a, b, ca, cb in zip(meta, L, R, Lc, Rc) if (a in NEVER or b in NEVER or ca in NEVER or cb in NEVER)]
print('touching never_move faces feats', len(set(never)))
pickle.dump(dict(feat=feat, S=S, meta=meta, L=L, R=R, Lc=Lc, Rc=Rc, istop=istop), open(cfg.work('chains.pkl'), 'wb'))
print('OK chains.pkl written')
