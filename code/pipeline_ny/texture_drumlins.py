import numpy as np, pandas as pd
d=pd.read_csv('drumlin_soils.csv'); d=d[(d.till_share>=0.5)&d.clay.notna()].copy()
d['tile']=(d.row//512).astype(int)*100+(d.col//512).astype(int)
d['logE']=np.log(d.elong); d['logL']=np.log(d.length_m); d['logW']=np.log(d.width_m)
# keep tiles with >=15 drumlins and >=2 distinct soil series (needed for within-tile contrast)
g=d.groupby('tile'); keep=g.filter(lambda x: len(x)>=15 and x.series.nunique()>=2).tile.unique(); d=d[d.tile.isin(keep)]
rng=np.random.default_rng(0); tiles=d.tile.unique(); idx_by=[np.where(d.tile.values==t)[0] for t in tiles]
def corr(x,y): return np.corrcoef(x,y)[0,1]
def demean(v): return v-d.groupby('tile')[v.name].transform('mean')
res=[]
for yv in ('logE','logL','logW'):
    for xv in ('clay','sand','frag'):
        x,y=d[xv].values,d[yv].values; xw,yw=demean(d[xv]).values,demean(d[yv]).values
        rA,rW=corr(x,y),corr(xw,yw); bA,bW=[],[]
        for _ in range(2000):
            idx=np.concatenate([idx_by[i] for i in rng.integers(0,len(tiles),len(tiles))])
            bA.append(corr(x[idx],y[idx])); bW.append(corr(xw[idx],yw[idx]))
        res.append(dict(y=yv,x=xv,r_across=rA,ci_across=np.percentile(bA,[2.5,97.5]),r_within=rW,ci_within=np.percentile(bW,[2.5,97.5])))
print(f"drumlins {len(d)} on till soils in {len(tiles)} tiles; within-tile texture SD: clay {demean(d.clay).std():.1f}%, sand {demean(d.sand).std():.1f}%, stones {demean(d.frag).std():.1f}%")
print(f"{'':6s}{'':6s} {'across field':>24s}   {'within tiles':>24s}")
for r in res:
    a,w=r['ci_across'],r['ci_within']
    flag=lambda c: '*' if (c[0]>0 or c[1]<0) else ' '
    print(f"{r['y']:6s}{r['x']:6s}  r={r['r_across']:5.2f} [{a[0]:5.2f},{a[1]:5.2f}]{flag(a)}   r={r['r_within']:5.2f} [{w[0]:5.2f},{w[1]:5.2f}]{flag(w)}")
# effect sizes within tiles: change per 10% stones / 10% sand
import statsmodels.formula.api as smf
for yv in ('logE','logL','logW'):
    f=smf.ols(f'{yv} ~ frag + sand + C(tile)',data=d).fit(cov_type='cluster',cov_kwds={'groups':d.tile})
    print(f"{yv}: within-tile per +10% stones {np.expm1(10*f.params['frag'])*100:+.1f}% (p={f.pvalues['frag']:.3f}); per +10% sand {np.expm1(10*f.params['sand'])*100:+.1f}% (p={f.pvalues['sand']:.3f})")
d.to_csv('drumlin_soils_till.csv',index=False)
