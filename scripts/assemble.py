# assemble.py  (stage 2, 2026-11-17; previous: bank.py runs, next: fix5.py)
# Purpose: build the new section set secs_new.json with three reaches:
#   N = asta principale sections up to S16130 (old names S00050..S16130 -> N00050..N16050, name = (index+1)*50; the user-edited sections
#       S00151/S01965 are kept as they are in the 50 m layers, with their hand-moved bankpoints);
#   V = first 60 sections of the Brenta vecchio (-> V00050..V03000);
#   B = Brenta downstream of Borgo (B00000..B17650) from the dpB/dpB2 placement (sec_in.json tag 'B') and bank_out.json;
#       a record with the key 'anchor' (dpB2.py: B00400 = idrometro_Borgo) becomes the nodestring itself.
#   The last N section (S16130 = N16050) is extended to the right channel using s16130/work/bank_out.json.
# Inputs : (cwd = WD) in/boundary_50m.gpkg, in/bankpoints_50m.gpkg, in/centerpoints_50m.gpkg (copies of the current layers),
#          work/cands.pkl and work/dpB.pkl (loaded but not used below), work/sec_in.json (B sections, after export_B/next_bed/obst),
#          work/bank_out.json (bank.py on the B sections), s16130/work/sec_in.json and s16130/work/bank_out.json (bank.py run for the S16130 extension;
#          the first record is the single section used).
# Output : WD/secs_new.json = list of dicts reach, old (old name or None), nome, s, [s_asta], cx, cy, coords (2 vertices), sides (sx/dx: x,y,z,dist_cp,tipo,regola,prom,moved);
#          prints the counts, some names and the bankpoints moved by hand (moved = distance between the section vertex and the layer bankpoint, m).
# Run    : cd WD ; python3 assemble.py      (Anaconda python3; relative paths: the working directory MUST be WD)
# Build the new section set: N (Caldonazzo-Borgo), V (Brenta vecchio), B (downstream of Borgo).
import json, pickle, numpy as np, geopandas as gpd, shapely, warnings; warnings.filterwarnings('ignore')
from shapely.geometry import LineString
# b = boundary (sections + nodestrings, index = fid); bp = bankpoints; cp = centerpoints of the current 50 m layers
b=gpd.read_file('in/boundary_50m.gpkg',fid_as_index=True); bp=gpd.read_file('in/bankpoints_50m.gpkg'); cp=gpd.read_file('in/centerpoints_50m.gpkg')
# C, D: loaded but never used in this script (harmless)
# S_/O = sec_in.json / bank_out.json of the B reach; X/XO = the single S16130 extension section and its right-side bank result
C=pickle.load(open('work/cands.pkl','rb'))['main']; D=pickle.load(open('work/dpB.pkl','rb'))
S_=json.load(open('work/sec_in.json')); O=json.load(open('work/bank_out.json'))
X=json.load(open('s16130/work/sec_in.json'))[0]; XO=json.load(open('s16130/work/bank_out.json'))[0]['R']
# secs = output list
secs=[]
# bprow: row of the bankpoint layer with a given name
def bprow(nm): return bp[bp.nome==nm].iloc[0]
# m / v = centerpoints of main (asta) / vecchio sorted by chainage s_m
m=cp[cp.stream=='main'].sort_values('s_m'); v=cp[cp.stream=='vecchio'].sort_values('s_m')
# N: asta sections up to s<=16130.01; V: first 60 vecchio sections
for reach,rows in (('N',m[m.s_m<=16130.01]),('V',v.iloc[:60])):
    for k,(i,r) in enumerate(rows.iterrows()):
        # g = the two vertices of the section (left end, right end); k+1 gives the new name
        g=shapely.get_coordinates(b[b.nome==r.nome].geometry.iloc[0])
        # for each end read the layer bankpoint; moved = how far it is from the section vertex (>0 means edited by hand)
        sides=[]
        for tag,pt in (('sx',g[0]),('dx',g[1])):
            q=bprow(f'{r.nome}_{tag}'); moved=float(np.hypot(q.geometry.x-pt[0],q.geometry.y-pt[1]))
            sides.append(dict(tag=tag,x=float(pt[0]),y=float(pt[1]),z=float(q.z_dtm),dist_cp=float(q.dist_cp),tipo=q.tipo,regola=q.regola,prom=None if q.prom!=q.prom else float(q.prom),moved=moved))
        # new record: new name f'{reach}{(k+1)*50:05d}', old name kept in 'old'
        secs.append(dict(reach=reach,old=r.nome,nome=f'{reach}{(k+1)*50:05d}',s=float(r.s_m),cx=r.geometry.x,cy=r.geometry.y,coords=g.tolist(),sides=sides))
# extended S16130 (last N section): new dx end
# S16130 (= N16050) must be secs[320]; a = left vertex (unchanged); u = unit vector towards the right (minus the normal); pdx = new right bankpoint = centre + u*t
last=secs[320]; assert last['old']=='S16130'
# replace the right vertex and its attributes (rule 'canale_dx', moved=-1 as a flag for 'new by extension')
a=np.array(last['coords'][0]); u=np.array([-X['nx'],-X['ny']]); pdx=np.array([X['x'],X['y']])+u*XO['t']
last['coords']=[a.tolist(),pdx.tolist()]
last['sides'][1].update(x=float(pdx[0]),y=float(pdx[1]),z=XO['z'],tipo=XO['kind'],regola='canale_dx',prom=XO['prom'],moved=-1.0,dist_cp=float(np.hypot(pdx[0]-last['cx'],pdx[1]-last['cy'])))
# B reach
# B reach: s0 = asta chainage of the first B section (B00000); s is made relative to it, s_asta keeps the old chainage
s0=None
for k,(s,o) in enumerate([(s,o) for s,o in zip(S_,O) if s['tag']=='B']):
    if s0 is None: s0=s['s']
    # p0 = left bankpoint = centre + n*t_L, p1 = right bankpoint = centre - n*t_R
    p0=np.array([s['x']+s['nx']*o['L']['t'],s['y']+s['ny']*o['L']['t']]); p1=np.array([s['x']-s['nx']*o['R']['t'],s['y']-s['ny']*o['R']['t']])
    # sides: attributes from bank_out.json (kind -> tipo, rule -> regola); moved = 0.0
    sides=[dict(tag=t,x=float(p[0]),y=float(p[1]),z=q['z'],dist_cp=q['t'],tipo=q['kind'],regola=q['rule'],prom=q['prom'],moved=0.0) for t,p,q in (('sx',p0,o['L']),('dx',p1,o['R']))]
    sec=dict(reach='B',old=None,nome=f'B{k*50:05d}',s=s['s']-s0,s_asta=s['s'],cx=s['x'],cy=s['y'],coords=[p0.tolist(),p1.tolist()],sides=sides)
    # anchor section (dpB2.py, key 'anchor' added by export_B.py): the section is the nodestring itself (e.g. idrometro_Borgo);
    # centre = its intersection with the centre line, ends = nodestring vertices, tipo 'nodestring', regola = nodestring name,
    # z = None (read from the DTM by write2.py), bank_out.json is ignored for this section
    if 'anchor' in s:
        a=s['anchor']; A=np.array(a['coords'])
        sec.update(s=a['s']-s0,s_asta=a['s'],cx=a['x'],cy=a['y'],coords=A.tolist(),
                   sides=[dict(tag=t,x=float(p[0]),y=float(p[1]),z=None,dist_cp=float(np.hypot(p[0]-a['x'],p[1]-a['y'])),tipo='nodestring',regola=a['nome'],prom=None,moved=0.0) for t,p in (('sx',A[0]),('dx',A[1]))])
        print('anchor section',sec['nome'],'=',a['nome'],'s',round(sec['s'],2))
    secs.append(sec)
# summary and the bankpoints moved by hand
print('sections',len(secs),{r:sum(x['reach']==r for x in secs) for r in 'NVB'}, secs[0]['nome'],secs[320]['nome'],secs[380]['nome'],secs[381]['nome'],secs[-1]['nome'])
print('bankpoints moved by user edits',[(x['old'],sd['tag'],round(sd['moved'],2)) for x in secs for sd in x['sides'] if sd['moved']>1e-6])
# save
json.dump(secs,open('secs_new.json','w'))
