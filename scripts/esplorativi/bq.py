# bq.py  (exploratory, NOT needed to produce the layers)
# Purpose: summarise the bankpoint results (bank_out.json) by reach of the main stream: counts of kinds, median top-to-top width W and bed width B,
#          distance bankpoint-to-top-of-bank, and print a sample of 'fallback' bankpoints in the reference reach s=4200-10200 m.
# Inputs : WD/work/sec_in.json (export_sec/next_bed) and WD/work/bank_out.json (bank.py). Output: print only.
# Run    : python3 bq.py WD      (Anaconda python3; does not import core.py)
import json, sys, numpy as np, collections
SP=sys.argv[1]
S=json.load(open(f'{SP}/work/sec_in.json')); O=json.load(open(f'{SP}/work/bank_out.json'))
rows=[(s,o) for s,o in zip(S,O)]
# rep(): statistics for stream `st` and abscissa range [a,b): Counter of bankpoint kinds (L and R together), median W (cL+cR) and B (tL+tR),
# and d = (distance of top-of-bank line) - (bankpoint distance) over both sides: its min and median (m).
def rep(a,b,st='main'):
    r=[(s,o) for s,o in rows if s['stream']==st and a<=s['s']<b]
    k=[o[x]['kind'] for s,o in r for x in 'LR']; c=collections.Counter(k)
    wid=[s['cL']+s['cR'] for s,o in r]; B=[s['tL']+s['tR'] for s,o in r]
    d=[]; 
    for s,o in r:
        for x in 'LR':
            tt=s['t'+x]; cc=s['c'+x]; d.append(cc-o[x]['t'])
    print(f"{st} {a:6d}-{b:6d} n={len(r):4d} {dict(c)} W med {np.median(wid):.1f} B med {np.median(B):.1f} t_to_top min/med {np.min(d):.2f} {np.median(d):.2f}")
# Reaches (s in m) for the main stream, then Brenta vecchio 0-4000 m.
for a,b in [(0,4200),(4200,10200),(10200,13200),(13200,17400),(17400,22800),(22800,34100)]: rep(a,b)
rep(0,4000,'vecchio')
# Print up to 14 fallback bankpoints in main s=4200-10200: toe, limit, top, bankpoint t, z, z at toe, z max in the window.
# sample fallback in ref reach
n=0
for s,o in rows:
    if s['stream']=='main' and 4200<=s['s']<10200:
        for x in 'LR':
            if o[x]['kind']=='fallback' and n<14:
                print(' sample',round(s['s']),x,'toe',round(s['t'+x],2),'lim',round(o[x]['limit'],2),'top',round(s['c'+x],2),'t',round(o[x]['t'],2),'z',round(o[x]['z'],2),'ztoe',round(o[x]['ztoe'],2),'zmax',round(o[x]['zrange'],2)); n+=1
