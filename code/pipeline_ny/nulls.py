"""Null distributions at the production window size, and re-scoring of NY windows."""
import sys, numpy as np, pandas as pd
sys.path.insert(0,'.')
from spectral import synthetic_field, analyze_window, fractal_noise
from validate import auc
WIN, DX, LMAX = 768, 20.0, 5000.0
def run(pl, n=50, hc=1.0):
    out=[]
    for i in range(n):
        rng=np.random.default_rng(7000+i); lat=rng.uniform(250,800)
        if pl=="noise":
            z=fractal_noise(WIN,DX,rng.uniform(2,3),rng.uniform(5,20),rng)
        else:
            z=synthetic_field(WIN,DX,lat_spacing=lat,long_spacing=3*lat,flow_az=rng.uniform(0,180),
              width=0.5*lat,elong=rng.uniform(2,4),height=12,placement=pl,jitter=0.18,
              noise_amp=rng.uniform(2,8),seed=8000+i,hc_factor=hc)
        r=analyze_window(z,DX,lam_max=LMAX); out.append(r)
    return pd.DataFrame(out)
R={k:run(k) for k in ("lattice","poisson","hardcore","noise")}
R["hardcore_tight"]=run("hardcore",hc=1.4)
for k,df in R.items():
    print(f"{k:15s} q_lat med {df.q_lat.fillna(0).median():.2f} p95 {df.q_lat.fillna(0).quantile(.95):.2f} | pk_lat med {df.pk_lat.median():.1f} p95 {df.pk_lat.quantile(.95):.1f}")
L=R["lattice"].q_lat.fillna(0)
for k in ("poisson","hardcore","hardcore_tight"):
    print(f"AUC q_lat lattice vs {k}: {auc(L,R[k].q_lat.fillna(0)):.2f}")
thr_q=max(R[k].q_lat.fillna(0).quantile(.95) for k in ("hardcore","hardcore_tight"))
thr_pk=R["noise"].pk_lat.quantile(.95)
d=pd.read_csv("ny_windows.csv")
dr=d[(d.pk_lat>thr_pk)&(d.anisotropy>0.7)]
print(f"\nNY: {len(d)} windows; drumlin terrain (pk_lat>{thr_pk:.1f} noise p95, anis>0.7): {len(dr)}")
print(f"  fraction with q_lat > hard-core 95th pct ({thr_q:.2f}): {(dr.q_lat.fillna(0)>thr_q).mean():.2f}  (5% expected if no extra order)")
np.save("data/null_thr_hc.npy",np.array([thr_q,thr_pk]))
