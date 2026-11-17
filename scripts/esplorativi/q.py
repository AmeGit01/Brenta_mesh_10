# q.py  (exploratory, NOT needed to produce the layers)
# Purpose: ad-hoc inspection: print name, mat_id and first coordinate of some region points, and first/last vertex, vertex count and whether it was
#          moved for some breakline fids (fids typed by hand, specific to the debugging done on 2026-11-09).
# Inputs : WD/in/regioni_ponti.gpkg, WD/work/chains.pkl, WD/work/widen2.pkl.  Output: print only.
# Run    : python3 q.py WD      (Anaconda python3; imports core.py from WD/work)
import sys; sys.path.insert(0,sys.argv[1]+'/work')
from core import *
r=gpd.read_file(f'{SP}/in/regioni_ponti.gpkg',fid_as_index=True)
for f in (89,114,81,90,116,57,58): print(f,r.nome[f],r.mat_id[f],r.geometry[f].coords[0][:2])
C=pickle.load(open(f'{SP}/work/chains.pkl','rb')); W2=pickle.load(open(f'{SP}/work/widen2.pkl','rb')); feat=C['feat']; nf=W2['newf']
for k in (1394,1405,1412,1423,979,1001,1061,1002):
    print(k,feat[k][0].round(1).tolist(),feat[k][-1].round(1).tolist(),'n',len(feat[k]),'moved' if k in nf else '')
