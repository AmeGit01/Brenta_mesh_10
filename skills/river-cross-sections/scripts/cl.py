# cl.py - raw centerlines of the river (and of its branches) as paths on a fine Voronoi skeleton of the bed polygon.
# Purpose: build a fine skeleton of the bed, with a cost that prefers the centre of the channel, and for every centerline of the
#          config section 'centerlines' find the path from its start to its end (through optional waypoints). A branch may end by
#          joining another centerline ('to': 'join:<name>').
# Inputs : work/graph.pkl (graph.py); the boundary layer of group 'in' (nodestrings named in the config; name field fields.boundary.name);
#          config section 'centerlines': list of {name, from, to, waypoints (optional), cost (optional), join_point (optional)}:
#            from/to      nodestring name (its centroid is used) or [x, y]; 'to' may also be 'join:<other centerline name>'
#            waypoints    ordered list of nodestring names or [x, y] points the path must pass through
#            cost         'centre' (default: cost length / distance from the bed boundary, follows the channel centre)
#                         or 'length' (plain shortest path)
#            join_point   only with 'join:': [x, y] or nodestring name where the branch ends on the other line (default: the node of
#                         the other line that is closest along the skeleton to the last waypoint)
#          config params.cl: bed_classes, buffer, min_island_area, seed_spacing, max_edge, min_boundary_dist, bridge_min_nodes,
#          bridge_max_gap, bridge_min_sep, bridge_cost_factor.
# Outputs: work/rawcl.pkl = dict(P = bed polygon, <centerline name> = Nx2 array of path vertices, ...); diagnostics on stdout.
# Run    : cd <WD> ; ~/anaconda3/bin/python3 <toolkit>/scripts/cl.py [-c rcs_config.json]
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common, geom
import pickle, numpy as np, shapely, geopandas as gpd, warnings
import networkx as nx
from scipy.spatial import Voronoi, cKDTree
from shapely.ops import unary_union
from shapely.geometry import Polygon
warnings.filterwarnings('ignore')

cfg = common.load(common.parser('raw centerlines on the Voronoi skeleton of the bed').parse_args())
pr = cfg['params']['cl']
# ---- read and validate the 'centerlines' section before any heavy work
CL = cfg.get('centerlines')
if not CL:
    raise SystemExit("config error: section 'centerlines' is missing (list of {name, from, to, waypoints}); fill it from the case material")
names = []
for i, c in enumerate(CL):
    for k in ('name', 'from', 'to'):
        if k not in c or c[k] in (None, '', []):
            raise SystemExit(f"config error: centerlines[{i}].{k} is missing" + (f" (line '{c['name']}')" if 'name' in c else ''))
    if c['name'] == 'P':
        raise SystemExit("config error: a centerline cannot be called 'P' (reserved key of rawcl.pkl)")
    if c['name'] in names:
        raise SystemExit(f"config error: duplicate centerline name '{c['name']}'")
    names.append(c['name'])
    if c.get('cost', 'centre') not in ('centre', 'length'):
        raise SystemExit(f"config error: centerlines[{i}].cost must be 'centre' or 'length'")
    if isinstance(c['to'], str) and c['to'].startswith('join:'):
        t = c['to'][5:]
        if t not in [x['name'] for x in CL] or t == c['name']:
            raise SystemExit(f"config error: centerlines[{i}].to = '{c['to']}' names no other centerline")
# order of computation: a branch that joins another line comes after it
order, todo = [], list(CL)
while todo:
    nxt = [c for c in todo if not (isinstance(c['to'], str) and c['to'].startswith('join:')) or c['to'][5:] in [o['name'] for o in order]]
    if not nxt:
        raise SystemExit("config error: circular 'join:' references in 'centerlines'")
    order += nxt; todo = [c for c in todo if c not in nxt]

faces, rows = geom.load_graph(cfg)
bedc = set(pr['bed_classes'])
bedf = [faces[r['face']] for r in rows if cfg.face_class(r['nome']) in bedc]
# bed = union of bed faces (small buffer closes gaps); prints area (m2) and centroid of its holes (islands)
bed = unary_union([f.buffer(pr['buffer']) for f in bedf])
print('interiors', [round(Polygon(i).area, 1) for i in bed.interiors], [[int(c) for c in Polygon(i).centroid.coords[0]] for i in bed.interiors])
# P = bed polygon with only the islands larger than min_island_area (smaller ones are filled)
P = Polygon(bed.exterior, [i for i in bed.interiors if Polygon(i).area > pr['min_island_area']])
# fine skeleton: Voronoi seeds along all rings of P
a = np.vstack([shapely.get_coordinates(shapely.line_interpolate_point(r, np.arange(0, r.length, pr['seed_spacing']))) for r in [P.exterior] + list(P.interiors)]); print('seeds', len(a))
V = Voronoi(a); vv = V.vertices; ins = shapely.contains_xy(P, vv[:, 0], vv[:, 1])
g = nx.Graph()
# dbd[k] = distance (m) from Voronoi vertex k to the nearest seed ~ distance to the bed boundary
kd = cKDTree(a); dbd, _ = kd.query(vv)
for p, q in V.ridge_vertices:
    if p >= 0 and q >= 0 and ins[p] and ins[q]:
        d = float(np.hypot(*(vv[p] - vv[q])))
        # w = length (m); c = cost = length / max(min boundary distance of the 2 vertices, floor): cheap in the middle of the channel
        if d < pr['max_edge']: g.add_edge(p, q, w=d, c=d / (max(min(dbd[p], dbd[q]), pr['min_boundary_dist']) ** 1.0))
cc = sorted(nx.connected_components(g), key=len, reverse=True); print('comps', [len(c) for c in cc[:6]])

# bridge secondary components (>= bridge_min_nodes nodes, e.g. strips separated by islands) to the others: link the two closest
# contacts (gap <= bridge_max_gap, at least bridge_min_sep apart) with edges of doubled cost
for c in cc[1:]:
    if len(c) < pr['bridge_min_nodes']: continue
    a = np.array(list(c)); ta = cKDTree(vv[a])
    others = np.array([n for cc2 in cc if cc2 is not c and len(cc2) >= pr['bridge_min_nodes'] for n in cc2])
    d, i = ta.query(vv[others])
    picked = []
    for j in np.argsort(d):
        if d[j] > pr['bridge_max_gap']: break
        p = vv[others[j]]
        if all(np.hypot(*(p - vv[others[k]])) > pr['bridge_min_sep'] for k in picked):
            picked.append(j); g.add_edge(int(others[j]), int(a[i[j]]), w=float(d[j]), c=float(d[j]) * pr['bridge_cost_factor'])
        if len(picked) == 2: break
    print('bridged comp', len(c), [round(float(d[j]), 2) for j in picked], [vv[others[j]].round().tolist() for j in picked])
cc = sorted(nx.connected_components(g), key=len, reverse=True); print('comps after', [len(c) for c in cc[:4]])
# H = main component; nodes/xy = node ids and coordinates; T = KD-tree of them
H = g.subgraph(cc[0]); nodes = np.array(list(H.nodes)); xy = vv[nodes]; T = cKDTree(xy)
bd = gpd.read_file(cfg.layer('in', 'boundary')).set_index(cfg.f('boundary', 'name'))


def pt(spec, where):
    """Point of a config spec: nodestring name -> centroid of that line, [x, y] -> itself."""
    if isinstance(spec, str):
        if spec not in bd.index:
            raise SystemExit(f"config error: nodestring '{spec}' (in {where}) not found in the boundary layer")
        return np.array(bd.geometry[spec].centroid.coords[0][:2])
    if isinstance(spec, (list, tuple)) and len(spec) == 2:
        return np.array([float(spec[0]), float(spec[1])])
    raise SystemExit(f"config error: {where} must be a nodestring name or [x, y]")


def nn(p):
    """Id of the skeleton node nearest to point p."""
    return int(nodes[T.query(p)[1]])


def pl(p):
    """Polyline length (m) of a node path."""
    a = vv[p]; return float(np.hypot(*np.diff(a, axis=0).T).sum())


paths = {}
for c in order:
    nm = c['name']; wkey = 'c' if c.get('cost', 'centre') == 'centre' else 'w'
    join = isinstance(c['to'], str) and c['to'].startswith('join:')
    wps = [pt(c['from'], f"centerlines['{nm}'].from")] + [pt(w, f"centerlines['{nm}'].waypoints[{k}]") for k, w in enumerate(c.get('waypoints', []))]
    if not join:
        wps.append(pt(c['to'], f"centerlines['{nm}'].to"))
    ids = [nn(p) for p in wps]
    print(nm, 'wp dist', [round(float(np.hypot(*(vv[i] - p))), 2) for i, p in zip(ids, wps)])
    path = []
    for a0, b0 in zip(ids[:-1], ids[1:]):
        p = nx.shortest_path(H, a0, b0, weight=wkey); path += p if not path else p[1:]
    if join:
        other = paths[c['to'][5:]]; last = path[-1]
        if 'join_point' in c:
            tgt = nn(pt(c['join_point'], f"centerlines['{nm}'].join_point"))
        else:
            # node of the other line closest to the last node along the skeleton
            dist = nx.single_source_dijkstra_path_length(H, last, weight='w')
            tgt = min((n for n in other if n in dist), key=lambda n: dist[n])
        conf = nx.shortest_path(H, last, tgt, weight='w'); path += conf[1:]
        kdm = cKDTree(vv[np.array(other)])
        print(nm, 'head/tail', vv[path[0]].round(1), vv[path[-1]].round(1), 'dist from', c['to'][5:], 'at end', round(float(kdm.query(vv[path[-1]])[0]), 2), 'at start', round(float(kdm.query(vv[path[0]])[0]), 2))
    paths[nm] = path
    print(nm, 'nodes', len(path), 'L', round(pl(path)))
# save raw centerlines (vertex coordinates, not yet smoothed/resampled), in config order
out = dict(P=P)
for c in CL: out[c['name']] = vv[paths[c['name']]]
pickle.dump(out, open(cfg.work('rawcl.pkl'), 'wb'))
