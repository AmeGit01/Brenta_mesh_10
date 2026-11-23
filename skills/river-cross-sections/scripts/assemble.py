# assemble.py - build the section set secs_new.json from the chosen stations and their bankpoints
# Purpose: one record per section from the left bankpoint to the right bankpoint (left to right looking downstream), named code + number
#          (number = first_number + k * sections.spacing), with the centre point, its chainage s, the distance to the next section
#          and the two bankpoints (z, distance from the centre, kind, rule, prominence). An anchored section is the nodestring itself
#          (its two vertices, kind bankpoint_values.nodestring, rule = nodestring name, z null = read from the DTM later).
# Inputs : work/sec_in.json (export_sec.py, after next_bed.py and obst.py) and work/bank_out.json (bank.py on it: same order, {L, R} with
#          t, z, kind, rule, prom); config: reaches[*] {code, source, first_number, chainage}, bankpoint_values {left, right, nodestring},
#          sections.name_pattern, params.assemble.side_overrides (optional list of {section, side: 'left'|'right', sec_in, bank_out, rule}:
#          the bankpoint of that side is replaced by the one computed for a pseudo-section, a file pair of the same format whose first
#          record is used, e.g. to extend a section into a second channel; the point is centre + t along the direction of the side).
# Outputs: work/secs_new.json = list of dicts reach, old (None), nome, number, source, s, [s_asta, s_src for reaches with chainage mode
#          cut_reference: s is then relative to the origin section], dist_next, cx, cy, coords (2 vertices: left, right), sides
#          (two dicts tag, x, y, z, dist_cp, tipo, regola, prom, moved; moved = -1 marks a side taken from an override). Prints counts.
# Run    : cd <WD> ; ~/anaconda3/bin/python3 <toolkit>/scripts/assemble.py [-c rcs_config.json]
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common
import json, numpy as np

cfg = common.load(common.parser('build secs_new.json from sec_in.json and bank_out.json').parse_args())
BV = cfg['bankpoint_values']; TL, TR = BV['left'], BV['right']
with open(cfg.work('sec_in.json')) as f: S = json.load(f)
with open(cfg.work('bank_out.json')) as f: O = json.load(f)
if len(S) != len(O):
    raise SystemExit(f'work/sec_in.json has {len(S)} sections but work/bank_out.json has {len(O)}: run bank.py on the current sec_in.json')
OV = cfg.get('params', {}).get('assemble', {}).get('side_overrides', [])
secs = []; by_reach = {rc['code']: [] for rc in cfg.reaches()}
for s, o in zip(S, O):
    by_reach[s['tag']].append((s, o))
for rc in cfg.reaches():
    code, rows = rc['code'], by_reach[rc['code']]
    if not rows: continue
    # sections of the reach in order; centre points, chainage
    recs = []
    for k, (s, o) in enumerate(rows):
        name = s.get('name') or cfg.section_name(code, rc['first_number'] + k * int(cfg['sections']['spacing']))
        n = np.array([s['nx'], s['ny']]); c = np.array([s['x'], s['y']])
        if 'anchor' in s:
            a = s['anchor']; A = np.array(a['coords']); c = np.array([a['x'], a['y']]); sv = a['s']
            sides = [dict(tag=t, x=float(p[0]), y=float(p[1]), z=None, dist_cp=float(np.hypot(*(p - c))), tipo=BV['nodestring'], regola=a['nodestring'],
                          prom=None, moved=0.0) for t, p in ((TL, A[0]), (TR, A[1]))]
            coords = A.tolist()
        else:
            sv = s['s']; p0 = c + n * o['L']['t']; p1 = c - n * o['R']['t']
            sides = [dict(tag=t, x=float(p[0]), y=float(p[1]), z=q['z'], dist_cp=q['t'], tipo=q['kind'], regola=q['rule'], prom=q['prom'], moved=0.0)
                     for t, p, q in ((TL, p0, o['L']), (TR, p1, o['R']))]
            coords = [p0.tolist(), p1.tolist()]
        recs.append(dict(reach=code, old=None, nome=name, number=rc['first_number'] + k * int(cfg['sections']['spacing']), source=rc['source'],
                         s=float(sv), cx=float(c[0]), cy=float(c[1]), coords=coords, sides=sides))
    # chainage within the reach: own = along the source centerline; cut_reference = relative to the origin section
    ch = rc['chainage']
    if ch['mode'] == 'cut_reference':
        o_ = [r for r in recs if r['nome'] == ch['origin_section']]
        if not o_: raise SystemExit(f"config error: reaches[{code}].chainage.origin_section {ch['origin_section']} is not a section of the reach")
        s0 = o_[0]['s']
        for r in recs: r['s_asta'] = r['s']; r['s_src'] = r['s']; r['s'] = r['s'] - s0
    for i, r in enumerate(recs): r['dist_next'] = recs[i + 1]['s'] - r['s'] if i + 1 < len(recs) else None
    secs += recs
# side overrides (a bankpoint of a pseudo-section replaces one side of a section)
BYN = {r['nome']: r for r in secs}
for ov in OV:
    r = BYN.get(ov['section'])
    if r is None: raise SystemExit(f"params.assemble.side_overrides: section {ov['section']} not in the set")
    with open(cfg.path(ov['sec_in'])) as f: X = json.load(f)[0]
    with open(cfg.path(ov['bank_out'])) as f: XO = json.load(f)[0]
    right = ov['side'] == 'right'; q = XO['R' if right else 'L']
    u = np.array([-X['nx'], -X['ny']]) if right else np.array([X['nx'], X['ny']])
    p = np.array([X['x'], X['y']]) + u * q['t']; sd = r['sides'][1 if right else 0]; ci = 1 if right else 0
    r['coords'][ci] = p.tolist()
    sd.update(x=float(p[0]), y=float(p[1]), z=q['z'], tipo=q['kind'], regola=ov['rule'], prom=q['prom'], moved=-1.0,
              dist_cp=float(np.hypot(p[0] - r['cx'], p[1] - r['cy'])))
    print('side override', ov['section'], ov['side'], 'rule', ov['rule'], 't', round(q['t'], 2))
names = [r['nome'] for r in secs]
ok = len(set(names)) == len(names) and all(cfg.is_section(n) for n in names)
for r in secs:
    if not all(np.isfinite([r['cx'], r['cy']])): ok = False
print('sections', len(secs), {c: len(v) for c, v in by_reach.items()}, names[0], names[-1])
print('anchored sections', [(r['nome'], r['sides'][0]['regola']) for r in secs if r['sides'][0]['tipo'] == BV['nodestring']])
print('OK' if ok else '**CHECK** duplicate or malformed section names')
with open(cfg.work('secs_new.json'), 'w') as f: json.dump(secs, f)
