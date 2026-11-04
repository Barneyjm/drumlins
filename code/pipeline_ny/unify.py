import numpy as np, pandas as pd, statsmodels.api as sm
m=pd.read_csv('tile_morph_till.csv').merge(pd.read_csv('icemodel/compare_g6.csv')[['tile','sp_full']],on='tile')
m['lu']=np.log(m.sp_full/100); m['lL']=np.log(m.L); m['lW']=np.log(m.W); m['lE']=np.log(m.L/m.W)
m['S']=(m.sand-m.sand.mean())/10      # per 10 % sand
m['F']=(m.frag-m.frag.mean())/10      # per 10 % stones
m['blk']=(m.r//2)*100+(m.c//2)
def ols(y,X): return np.linalg.lstsq(X,y,rcond=None)[0]
def design(d,cols): return np.c_[np.ones(len(d)),d[cols].values]
# --- unconstrained
U={}
for yv in ('lL','lW'):
    U[yv]=ols(m[yv].values,design(m,['lu','S','F']))
# --- constrained two-factor: lL = a + alpha*lu + g_S*S + g_F*F ; lW = b + g_S*S + g_F*F  (shared texture, no speed in W)
def fit_constrained(d):
    n=len(d); Y=np.r_[d.lL.values,d.lW.values]
    X=np.zeros((2*n,5)); X[:n,0]=1; X[n:,1]=1; X[:n,2]=d.lu; X[:,3]=np.r_[d.S,d.S]; X[:,4]=np.r_[d.F,d.F]
    return ols(Y,X)   # a, b, alpha, gS, gF
cC=fit_constrained(m)
# --- spatial block CV (leave one 2x2-tile block out)
def cv(kind):
    pred={k:np.zeros(len(m)) for k in ('lL','lW','lE')}
    for b in m.blk.unique():
        tr=m[m.blk!=b]; te=m.blk==b; d=m[te]
        if kind=='mean':
            pL=np.full(te.sum(),tr.lL.mean()); pW=np.full(te.sum(),tr.lW.mean())
        elif kind=='unconstrained':
            pL=design(d,['lu','S','F'])@ols(tr.lL.values,design(tr,['lu','S','F'])); pW=design(d,['lu','S','F'])@ols(tr.lW.values,design(tr,['lu','S','F']))
        elif kind=='speed_only':
            pL=design(d,['lu'])@ols(tr.lL.values,design(tr,['lu'])); pW=np.full(te.sum(),tr.lW.mean())
        else:
            a,bb,al,gS,gF=fit_constrained(tr); pL=a+al*d.lu+gS*d.S+gF*d.F; pW=bb+gS*d.S+gF*d.F
        pred['lL'][te.values]=pL; pred['lW'][te.values]=pW; pred['lE'][te.values]=np.asarray(pL)-np.asarray(pW)
    return {k:1-np.sum((m[k]-pred[k])**2)/np.sum((m[k]-m[k].mean())**2) for k in pred}
print(f"{len(m)} tiles; out-of-sample R^2 (leave-one-block-out):")
for k in ('mean','speed_only','unconstrained','two-factor'):
    r=cv(k); print(f"  {k:14s} length {r['lL']:+.2f}  width {r['lW']:+.2f}  elongation {r['lE']:+.2f}")
# --- bootstrap CIs for the two-factor law (resample blocks)
rng=np.random.default_rng(0); ub=m.blk.unique(); bs=[]
for _ in range(3000):
    idx=np.concatenate([np.where(m.blk==b)[0] for b in rng.choice(ub,len(ub))]); bs.append(fit_constrained(m.iloc[idx]))
bs=np.array(bs); lo,hi=np.percentile(bs,[2.5,97.5],axis=0)
a,b,al,gS,gF=cC
names=['ln L0','ln W0','alpha (speed exponent)','gamma_sand (per 10%)','gamma_stones (per 10%)']
for nm,v,l,h in zip(names,cC,lo,hi): print(f"  {nm:24s} {v:+.3f}  [{l:+.3f}, {h:+.3f}]")
print(f"\nL0 = {np.exp(a):.0f} m, W0 = {np.exp(b):.0f} m at u = 100 m/a and field-mean texture (sand {m.sand.mean():.0f}%, stones {m.frag.mean():.0f}%)")
print('unconstrained coefficients (const, ln u, sand/10, stones/10):'); 
for k,v in U.items(): print('  ',k,np.round(v,3))
