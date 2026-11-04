import numpy as np, pandas as pd, statsmodels.formula.api as smf
from scipy import stats
ALPHA_NY,LO_NY,HI_NY=0.491,0.265,0.859
def neff(x,y,D):
    zx=(x-x.mean())/x.std(); zy=(y-y.mean())/y.std(); n=len(x); acc=0
    for b in range(6):
        m=(D>b)&(D<=b+1)
        if m.sum(): acc+=m.sum()*(zx[:,None]*zx[None,:])[m].mean()*(zy[:,None]*zy[None,:])[m].mean()
    return n**2/(n+acc)
rng=np.random.default_rng(0)
for thr in ('0.5',):
  for path in (15,20):
    d=pd.read_csv(f'tile_conv_{thr}_{path}km.csv').merge(pd.read_csv(f'tile_morph_{thr}.csv')[['tile','L','W','E','n','r','c']],on='tile')
    d['lE'],d['lL'],d['lW']=np.log(d.E),np.log(d.L),np.log(d.W); d['xs'],d['ys']=(d.x-d.x.mean())/1e4,(d.y-d.y.mean())/1e4
    D=np.hypot(d.r.values[:,None]-d.r.values[None,:],d.c.values[:,None]-d.c.values[None,:]); blk=(d.r//2)*100+(d.c//2); ub=blk.unique()
    out=[]
    for yv in ('lE','lL','lW'):
        r=np.corrcoef(d.conv,d[yv])[0,1]; ne=neff(d.conv.values,d[yv].values,D); p=2*stats.t.sf(abs(r*np.sqrt((ne-2)/(1-r**2))),max(ne-2,1))
        sl=np.polyfit(d.conv,d[yv],1)[0]; bs=[]
        for _ in range(3000):
            idx=np.concatenate([np.where(blk==b)[0] for b in rng.choice(ub,len(ub))]); bs.append(np.polyfit(d.conv.values[idx],d[yv].values[idx],1)[0])
        lo,hi=np.percentile(bs,[2.5,97.5])
        rx=smf.ols('conv ~ coh + xs + ys',d).fit().resid; ry=smf.ols(f'{yv} ~ coh + xs + ys',d).fit().resid; rp=np.corrcoef(rx,ry)[0,1]
        out.append(f"{yv[1]}: r={r:5.2f} (p={p:.3f}, n_eff {ne:4.1f}) slope {sl:+.2f} [{lo:+.2f},{hi:+.2f}] partial r={rp:5.2f}")
    print(f"threshold {thr}, {path} km path, {len(d)} tiles"); [print('   '+o) for o in out]
print(f"\nNew York: elongation slope alpha = {ALPHA_NY} [{LO_NY}, {HI_NY}]; length carries it, width ~0")
