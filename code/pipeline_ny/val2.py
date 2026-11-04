import sys, numpy as np
sys.path.insert(0,'.')
from spectral import synthetic_field, analyze_window
from validate import angdiff, auc
for N, lmax in ((512,3000),(512,5000),(768,5000)):
    res={"lattice":[],"poisson":[]}; errs=[]
    for i in range(30):
        rng=np.random.default_rng(1000+i); lat=rng.uniform(300,800); az=rng.uniform(0,180)
        kw=dict(lat_spacing=lat,long_spacing=3*lat,flow_az=az,width=0.5*lat,elong=3,height=12,noise_amp=rng.uniform(2,8),seed=2000+i,jitter=0.18)
        for pl in res:
            r=analyze_window(synthetic_field(N,20.0,placement=pl,**kw),20.0,lam_max=lmax); res[pl].append(r)
            if pl=="lattice": errs.append((angdiff(r['flow_az'],az),abs(r['lam_lat']-lat)/lat,abs(r['lam_long']-3*lat)/(3*lat)))
    e=np.array(errs)
    print(f"N={N} lmax={lmax}: az med {np.median(e[:,0]):.1f} p90 {np.percentile(e[:,0],90):.1f} | lat med {np.median(e[:,1])*100:.1f}% p90 {np.percentile(e[:,1],90)*100:.0f}% | long med {np.median(e[:,2])*100:.1f}% p90 {np.percentile(e[:,2],90)*100:.0f}%")
    for k in ("q_lat","q_long","pk_long","reg_lat"):
        L=np.nan_to_num([r[k] for r in res['lattice']]);P=np.nan_to_num([r[k] for r in res['poisson']])
        print(f"   {k}: lattice {np.median(L):.2f} poisson {np.median(P):.2f} AUC {auc(L,P):.2f}")
