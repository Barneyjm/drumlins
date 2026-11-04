import sys, numpy as np
sys.path.insert(0,'.')
from spectral import synthetic_field
from detect import detect
from scipy.spatial import cKDTree
N,DX=512,20.0
for pl in ("lattice","hardcore"):
    rec,prec,azerr=[],[],[]
    for i in range(12):
        rng=np.random.default_rng(300+i); lat=rng.uniform(300,700); az=rng.uniform(0,180)
        z,ctr=synthetic_field(N,DX,lat_spacing=lat,long_spacing=3*lat,flow_az=az,width=0.5*lat,elong=3,height=12,
              placement=pl,jitter=0.18,noise_amp=rng.uniform(2,6),seed=400+i,return_centers=True)
        lab,P=detect(z,DX,flow_az=az)
        det=np.array([[p['row'],p['col']] for p in P]) if P else np.zeros((0,2))
        inner=lambda a:(a[:,0]>40)&(a[:,0]<N-40)&(a[:,1]>40)&(a[:,1]<N-40)
        t=ctr[inner(ctr)]; dd=det[inner(det)] if len(det) else det
        tol=0.35*lat/DX
        if len(dd):
            d1,_=cKDTree(dd).query(t); d2,_=cKDTree(t).query(dd)
            rec.append((d1<tol).mean()); prec.append((d2<tol).mean())
        azerr+= [min(abs(p['az']-az)%180,180-abs(p['az']-az)%180) for p in P]
    print(f"{pl}: recall {np.mean(rec):.2f}  precision {np.mean(prec):.2f}  median az err {np.median(azerr):.1f} deg")
