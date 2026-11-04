import numpy as np, pandas as pd
from scipy import stats
def neff(x,y,D,maxlag=6):
    zx=(x-x.mean())/x.std(); zy=(y-y.mean())/y.std(); n=len(x); acc=0.0
    for b0,b1 in zip(range(maxlag),range(1,maxlag+1)):
        m=(D>b0)&(D<=b1)
        if m.sum(): acc+=m.sum()*(zx[:,None]*zx[None,:])[m].mean()*(zy[:,None]*zy[None,:])[m].mean()
    return n**2/(n+acc)
rng=np.random.default_rng(0)
for sg in (3,4,6):
    t=pd.read_csv(f'tile_flow_{sg}km.csv'); t['r']=t.tile//100; t['c']=t.tile%100
    D=np.hypot(t.r.values[:,None]-t.r.values[None,:],t.c.values[:,None]-t.c.values[None,:])
    blk=(t.r//2)*100+(t.c//2); ub=blk.unique()
    print(f"\nsmoothing {sg} km ({len(t)} tiles)")
    for xv,lab in (('div_local','local flowline divergence (+ = spreading)'),('logw','upstream log flux-tube width'),('speed_proxy','speed proxy = 1/width')):
        for yv in ('E','L','W'):
            x=t[xv].values; y=np.log(t[yv].values); r=np.corrcoef(x,y)[0,1]; ne=neff(x,y,D)
            p=2*stats.t.sf(abs(r*np.sqrt((ne-2)/(1-r**2))),max(ne-2,1))
            bs=[]
            for _ in range(3000):
                idx=np.concatenate([np.where(blk==b)[0] for b in rng.choice(ub,len(ub))]); bs.append(np.corrcoef(x[idx],y[idx])[0,1])
            lo,hi=np.percentile(bs,[2.5,97.5])
            if yv=='E' or xv=='speed_proxy':
                print(f"  {lab:42s} vs log {yv}: r={r:5.2f} [{lo:5.2f},{hi:5.2f}] n_eff={ne:4.1f} p={p:.3f}")
