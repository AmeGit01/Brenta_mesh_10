# check_angles.py - read-only check of the angle rule on the derived layers, compared with the original layers
# Purpose: no angle sharper than rules.min_angle_deg may exist inside a line (spike between two consecutive segments) or where two lines
#          meet (crossing, T-junction, shared end), for breaklines, nodestrings and sections. Angles that already exist in the original
#          layers (both lines identical there) are PRE-EXISTING: they are listed and counted, but they do not fail the check.
#          Lines that run together over a stretch within 1 mm for more than 0.5 m (e.g. a breakline laid on a section or nodestring) have no angle and are skipped.
#          An angle is NEW when it involves a section, or a line whose geometry differs from the original layer (or that is not in it).
#          Lines are matched with the originals by id: breaklines by fid, boundary lines (nodestrings) by name.
#          The check is OK only if every NEW acute angle is covered by an entry of exceptions.angle.
# Inputs : cfg layers ('out', breaklines|boundary) = derived layers, cfg layers ('in', breaklines|boundary) = originals,
#          cfg fields.boundary.name, cfg sections.name_pattern, cfg['rules']['min_angle_deg'],
#          cfg['exceptions']['angle'] = [{"where": [x, y] | [id, ...], "reason", "date"}]. An entry with two numbers matches an angle
#          located within 0.01 m of that point; an entry with ids matches an angle whose lines are all in the list (an integer is a
#          breakline fid, a string is a boundary-line name).
# Output : print only (counts, lists of NEW and of accepted angles, number of PRE-EXISTING angles; it never changes any data).
# Run    : cd <WD> ; ~/anaconda3/bin/python3 <toolkit>/scripts/check_angles.py [-c rcs_config.json] [--list-pre]     (geo interpreter)
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common
import numpy as np, geopandas as gpd, shapely, warnings; warnings.filterwarnings('ignore')
import geom

EXC_XY_TOL = 0.01      # m: an exception given as a point matches angles located this close to it


def _lines(cfg, which):
    """{id: coords}: breaklines by fid (int), boundary lines by name (str). Null/empty geometries are skipped."""
    out = {}
    bl = gpd.read_file(cfg.layer(which, 'breaklines'), fid_as_index=True)
    for f, g in bl.geometry.items():
        if g is not None and not g.is_empty:
            out[int(f)] = shapely.get_coordinates(g)[:, :2]
    bd = gpd.read_file(cfg.layer(which, 'boundary'), fid_as_index=True)
    for n, g in zip(bd[cfg.f('boundary', 'name')], bd.geometry):
        if g is not None and not g.is_empty:
            out[str(n)] = shapely.get_coordinates(g)[:, :2]
    return out


def _same(a, b):
    return a is not None and len(a) == len(b) and np.abs(np.asarray(a) - np.asarray(b)).max() < 1e-6


def _excepted(cfg, ids, xy):
    """True if an entry of exceptions.angle covers the angle. where = [x, y] (two floats: a point) or a list of ids."""
    for e in cfg.exc_angle():
        w = e['where']
        if len(w) == 2 and all(isinstance(v, float) for v in w):
            if np.hypot(xy[0] - w[0], xy[1] - w[1]) <= EXC_XY_TOL:
                return True
        elif all(i in w for i in ids):
            return True
    return False


def angle_report(cfg):
    """Run the check. Returns a dict: min_deg, new (list of items), pre (list), accepted (list); an item is
    (kind, ids, (x, y), angle) with kind 'spike' (ids = [line]) or 'meet' (ids = [line1, line2])."""
    MIN = cfg.min_angle()
    der = _lines(cfg, 'out'); org = _lines(cfg, 'in')
    isnew = lambda i: (isinstance(i, str) and cfg.is_section(i)) or not _same(org.get(i), der[i])
    spikes, meets = geom.acute_angles(der, MIN)
    # two lines that run together over a stretch (a breakline laid on a section or a nodestring) have no angle there: skipped
    meets = [m for m in meets if not common.run_together(der[m[0]], der[m[1]])]
    items = [('spike', [i], tuple(der[i][k]), a) for i, k, a in spikes] + [('meet', [i, j], (x, y), a) for i, j, x, y, a in meets]
    new, pre, acc = [], [], []
    for it in items:
        if any(isnew(i) for i in it[1]):
            (acc if _excepted(cfg, it[1], it[2]) else new).append(it)
        else:
            pre.append(it)
    return dict(min_deg=MIN, n_lines=len(der), new=new, pre=pre, accepted=acc)


def fmt(it):
    kind, ids, (x, y), a = it
    return f"{kind} {'/'.join(map(str, ids))} at ({x:.2f}, {y:.2f}) {a:.1f} deg"


if __name__ == '__main__':
    ap = common.parser('check the angle rule on the derived layers')
    ap.add_argument('--list-pre', action='store_true', help='also list the PRE-EXISTING angles')
    args = ap.parse_args(); cfg = common.load(args)
    r = angle_report(cfg)
    print(f"lines examined {r['n_lines']}; minimum angle {r['min_deg']:g} deg")
    print(f"PRE-EXISTING acute angles (identical in the originals, not counted): {len(r['pre'])}"
          f" (spikes {sum(i[0] == 'spike' for i in r['pre'])}, meetings {sum(i[0] == 'meet' for i in r['pre'])})")
    if args.list_pre:
        for it in sorted(r['pre'], key=lambda t: t[3]): print('  ', fmt(it))
    print(f"accepted by exceptions.angle: {len(r['accepted'])}")
    for it in r['accepted']: print('  ', fmt(it))
    print(f"NEW acute angles: {len(r['new'])} (spikes {sum(i[0] == 'spike' for i in r['new'])}, meetings {sum(i[0] == 'meet' for i in r['new'])},"
          f" involving a section {sum(any(isinstance(j, str) and cfg.is_section(j) for j in i[1]) for i in r['new'])})")
    for it in sorted(r['new'], key=lambda t: t[3]): print('  ', fmt(it))
    print('angle rule: no new angle < %g deg' % r['min_deg'], 'OK' if not r['new'] else '**CHECK**')
