# skel.py - Voronoi skeleton (medial axis) of the riverbed as a networkx graph (coarse first version).
# Purpose: from the planar graph, merge the bed faces, sample their outline and keep the Voronoi edges inside the bed. The finer
#          skeleton that the centerlines use is recomputed by cl.py; this one is a diagnostic / first-version skeleton.
# Inputs : work/graph.pkl (graph.py); config params.skel: bed_classes, corridor_classes, buffer, seed_spacing, max_edge
#          (face classes are those of cfg.face_class).
# Outputs: work/skel.pkl = dict(bed, cor, g, vv); diagnostics on stdout.
# Run    : cd <WD> ; ~/anaconda3/bin/python3 <toolkit>/scripts/skel.py [-c rcs_config.json]
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common, geom
import pickle, numpy as np, shapely, warnings, networkx as nx
warnings.filterwarnings('ignore')
from shapely.ops import unary_union
from shapely.geometry import LineString
from scipy.spatial import Voronoi

cfg = common.load(common.parser('Voronoi skeleton of the bed polygon').parse_args())
pr = cfg['params']['skel']
faces, rows = geom.load_graph(cfg)
bedc, corc = set(pr['bed_classes']), set(pr['corridor_classes'])
isbed = lambda n: cfg.face_class(n) in bedc
iscor = lambda n: cfg.face_class(n) in corc
buf = pr['buffer']
# bed = union of bed faces, each buffered so that adjacent faces fuse despite rounding gaps
bed = unary_union([faces[r['face']].buffer(buf) for r in rows if isbed(r['nome'])])
# cor = union of the corridor faces (bed + banks + walls), same buffer
cor = unary_union([faces[r['face']].buffer(buf) for r in rows if iscor(r['nome'])])
print('bed', bed.geom_type, len(getattr(bed, 'geoms', [bed])), round(bed.area / 1e4, 1), 'cor', cor.geom_type, len(getattr(cor, 'geoms', [cor])), round(cor.area / 1e4, 1))
parts = sorted(getattr(bed, 'geoms', [bed]), key=lambda p: -p.area)
for p in parts[:8]: print(' bedpart', round(p.area), [int(x) for x in p.bounds], len(p.interiors))
# P = the polygon used for the skeleton: the single part, otherwise the whole multipart bed
P = parts[0] if len(parts) == 1 else bed
# Voronoi seeds sampled along every ring (exterior and holes) of P
sp = pr['seed_spacing']; pts = []
for ring in ([P.exterior] + list(P.interiors) if P.geom_type == 'Polygon' else [r for q in P.geoms for r in [q.exterior] + list(q.interiors)]):
    L = ring.length; n = int(L / sp) + 1
    pts.append(shapely.get_coordinates(shapely.line_interpolate_point(ring, np.linspace(0, L, n, endpoint=False))))
pts = np.vstack(pts); print('seeds', len(pts))
V = Voronoi(pts); vv = V.vertices
# Voronoi vertices inside the polygon approximate the medial axis
inside = shapely.contains_xy(P, vv[:, 0], vv[:, 1])
g = nx.Graph()
for a, b in V.ridge_vertices:
    if a >= 0 and b >= 0 and inside[a] and inside[b]:
        # keep only short ridges fully inside P; edge weight = length
        d = float(np.hypot(*(vv[a] - vv[b])))
        if d < pr['max_edge'] and P.contains(LineString([vv[a], vv[b]])): g.add_edge(a, b, weight=d)
cc = sorted(nx.connected_components(g), key=len, reverse=True); print('skeleton comps', [len(c) for c in cc[:6]])
pickle.dump(dict(bed=bed, cor=cor, g=g, vv=vv), open(cfg.work('skel.pkl'), 'wb'))
