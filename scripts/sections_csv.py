# sections_csv.py  (stage 3, 2026-11-18; after write2.py/verify2.py)
# Purpose: write the summary table of the sections (one row per section) from the 50 m layers read back from disk:
#          sezione, ramo, s_m (chainage within the reach, from centerpoints), for each side z_dtm, dist_cp, tipo, regola, prom (from bankpoints),
#          and lunghezza_m (length of the section line in boundary). Rows follow the order of the boundary layer (N, V, B).
# Inputs : argv[1] = layers folder (e.g. layers), containing boundary_50m.gpkg, centerpoints_50m.gpkg, bankpoints_50m.gpkg
#          (argv[2], optional = suffix inserted before .gpkg, e.g. _backup_20261118, to read the backups instead).
# Output : argv[3] (optional, default docs/Brenta_sections_50m_mesh10.csv) OVERWRITTEN; prints the number of rows.
# Run    : python3 scripts/sections_csv.py layers "" docs/Brenta_sections_50m_mesh10.csv      (Anaconda python3, from the project folder)
# Rounding: s_m 2 decimals, z 3, dist_cp 2, prom 3, length 2; empty field for null values.
import sys, csv, geopandas as gpd, shapely, warnings; warnings.filterwarnings('ignore')
L=sys.argv[1]; suf=sys.argv[2] if len(sys.argv)>2 else ''; outf=sys.argv[3] if len(sys.argv)>3 else 'docs/Brenta_sections_50m_mesh10.csv'
b=gpd.read_file(f'{L}/boundary_50m{suf}.gpkg'); cp=gpd.read_file(f'{L}/centerpoints_50m{suf}.gpkg'); bp=gpd.read_file(f'{L}/bankpoints_50m{suf}.gpkg')
# sections = boundary features named letter + 5 digits; s = chainage per section; side = bankpoint row per name
sec=b[b.nome.str.match(r'^[NVB]\d{5}$')]; s=dict(zip(cp.nome,cp.s_m)); side={r.nome:r for r in bp.itertuples()}
# f(x, n): rounded number or empty string for null/NaN
def f(x,n): return '' if x is None or x!=x else round(float(x),n)
rows=[]
for nm,g in zip(sec.nome,sec.geometry):
    r=[nm,nm[0],f(s[nm],2)]
    for t in ('sx','dx'):
        q=side[f'{nm}_{t}']; r+=[f(q.z_dtm,3),f(q.dist_cp,2),q.tipo,q.regola,f(q.prom,3)]
    r.append(f(shapely.length(g),2)); rows.append(r)
with open(outf,'w',newline='') as fh:
    w=csv.writer(fh); w.writerow(['sezione','ramo','s_m','z_sx','dist_cp_sx','tipo_sx','regola_sx','prom_sx','z_dx','dist_cp_dx','tipo_dx','regola_dx','prom_dx','lunghezza_m']); w.writerows(rows)
print('rows',len(rows),'->',outf)
