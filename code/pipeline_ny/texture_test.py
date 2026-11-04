import numpy as np, pandas as pd
from scipy import stats
m=pd.read_csv('tile_morph.csv').merge(pd.read_csv('tile_till.csv'),on='tile')
m['r']=m.tile//100; m['c']=m.tile%100
m['logE']=np.log(m.E); m['logL']=np.log(m.L); m['logW']=np.log(m.W)
D=np.hypot(m.r.values[:,None]-m.r.values[None,:], m.c.values[:,None]-m.c.values[None,:])
def moran(x):
    z=x-x.mean(); w=((D>0)&(D<=1.5)).astype(float); return (len(x)/w.sum())*(z@w@z)/(z@z)
def neff(x,y,maxlag=6):
    # Dutilleul (1993)-style effective n from distance-class autocorrelations
    zx=(x-x.mean())/x.std(); zy=(y-y.mean())/y.std(); n=len(x)
    bins=np.arange(0,maxlag+1); sx=sy=0.0; tot=0
    acc=0.0
    for b0,b1 in zip(bins[:-1],bins[1:]):
        m_=(D>b0)&(D<=b1); k=m_.sum()
        if k==0: continue
        rx=(zx[:,None]*zx[None,:])[m_].mean(); ry=(zy[:,None]*zy[None,:])[m_].mean()
        acc+=k*rx*ry
    return n**2/(n+acc)
rng=np.random.default_rng(0)
blk=(m.r//2)*100+(m.c//2); ub=blk.unique()
def boot(x,y,B=4000):
    out=[]
    for _ in range(B):
        pick=rng.choice(ub,len(ub)); idx=np.concatenate([np.where(blk==b)[0] for b in pick])
        if np.std(x[idx])>0 and np.std(y[idx])>0: out.append(np.corrcoef(x[idx],y[idx])[0,1])
    return np.percentile(out,[2.5,97.5])
print(f"tiles {len(m)} | Moran's I: elongation {moran(m.logE.values):.2f}, clay {moran(m.clay.values):.2f}, sand {moran(m.sand.values):.2f}, stones {moran(m.frag.values):.2f}")
print(f"texture ranges: clay {m.clay.min():.0f}-{m.clay.max():.0f}%, sand {m.sand.min():.0f}-{m.sand.max():.0f}%, stones/gravel {m.frag.min():.0f}-{m.frag.max():.0f}% by volume")
print(f"\n{'':10s}{'vs':>4} {'r':>6} {'95% CI (block bootstrap)':>26} {'n_eff':>6} {'p (n_eff)':>9}")
for yv in ('logE','logL','logW'):
    for xv in ('clay','sand','frag','till_frac'):
        x=m[xv].values; y=m[yv].values; r=np.corrcoef(x,y)[0,1]; ne=neff(x,y)
        t=r*np.sqrt((ne-2)/(1-r**2)); p=2*stats.t.sf(abs(t),max(ne-2,1)); lo,hi=boot(x,y)
        print(f"{yv:10s}{xv:>10s} {r:6.2f}   [{lo:5.2f}, {hi:5.2f}]          {ne:5.1f}   {p:7.3f}")
import statsmodels.api as sm
X=sm.add_constant(m[['clay','sand','frag']]); fit=sm.OLS(m.logE,X).fit()
print('\nmultiple regression log(elongation) ~ clay + sand + stones: R2 %.2f'%fit.rsquared); print(fit.params.round(4).to_string())
m.to_csv('tile_morph_till.csv',index=False)
