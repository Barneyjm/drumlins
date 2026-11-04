import sys, numpy as np, pandas as pd, rasterio
from multiprocessing import Pool
from scipy import ndimage as ndi
sys.path.insert(0,'/home/claude/drumlins')
from detect import detect, tophat_relief
from pointtest import object_shuffle_test
T, DX = 512, 20.0
with rasterio.open('data/ny_dem_20m.tif') as s:
    Z=s.read(1); WATER=s.read(2)>0.5; TR=s.transform
VALID=np.isfinite(Z)&~WATER
zz=np.where(VALID,Z,0.0); num=ndi.gaussian_filter(zz,25); den=ndi.gaussian_filter(VALID.astype(float),25)
ZF=np.where(VALID,Z,num/np.maximum(den,1e-6))
W=pd.read_csv('ny_windows.csv')
def flow_at(r,c):
    d=(W.row+384-r)**2+(W.col+384-c)**2; return float(W.flow_az.iloc[int(np.argmin(d.values))])
def job(rc):
    r,c=rc; v=VALID[r:r+T,c:c+T]
    if v.mean()<0.6: return None
    z=ZF[r:r+T,c:c+T]; fa=flow_at(r+T/2,c+T/2)
    lab,P=detect(z,DX,valid=v,flow_az=fa,half_frac=0.5)
    th=tophat_relief(z,DX)
    res=object_shuffle_test(th,lab,v,DX,nsim=39,seed=r*7+c)
    if res is None: return dict(row=r,col=c,n=len(P),skipped=1)
    x,y=TR*(c+T/2,r+T/2)
    res.update(row=r,col=c,x=x,y=y,valid=float(v.mean()),flow_in=fa,
               med_len=float(np.median([p['length_m'] for p in P])) if P else np.nan,
               med_wid=float(np.median([p['width_m'] for p in P])) if P else np.nan,skipped=0)
    return res
if __name__=='__main__':
    H,Wd=Z.shape
    tiles=[(r,c) for r in range(0,H-T+1,T) for c in range(0,Wd-T+1,T)]
    with Pool(int(sys.argv[1])) as p: out=[o for o in p.map(job,tiles) if o]
    df=pd.DataFrame(out); df.to_csv('ny_tiles_shuffle.csv',index=False)
    t=df[df.skipped==0]
    print(f"tiles tested {len(t)} (skipped {int(df.skipped.sum())}), drumlins {int(t.n.sum())}")
    print(f"p_pk<0.05: {(t.p_pk<0.05).sum()} ({(t.p_pk<0.05).mean():.2f}; ~0.08 expected by chance)")
    print(f"p_q <0.05: {(t.p_q<0.05).sum()} ({(t.p_q<0.05).mean():.2f}; ~0.01 expected)")
    print(f"median pk_obs/pk_null {np.median(t.pk_obs/t.pk_null_med):.2f}, median q_obs {t.q_obs.median():.2f} vs null {t.q_null_med.median():.2f}")
