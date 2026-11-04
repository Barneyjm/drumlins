import sys, numpy as np
sys.path.insert(0,'.')
from spectral import synthetic_field
from detect import detect, tophat_relief
from pointtest import object_shuffle_test
N,DX=512,20.0
hf=float(sys.argv[1]); pl=sys.argv[2]; jit=float(sys.argv[3]); ns=int(sys.argv[4])
pq=[];pp=[];fill=[]
for i in range(ns):
    off=int(sys.argv[5]) if len(sys.argv)>5 else 0; hc=float(sys.argv[6]) if len(sys.argv)>6 else 1.0; rng=np.random.default_rng(900+i+off); lat=rng.uniform(300,700); az=rng.uniform(0,180)
    z=synthetic_field(N,DX,lat_spacing=lat,long_spacing=3*lat,flow_az=az,width=0.5*lat,elong=3,height=12,
          placement=pl,jitter=jit,noise_amp=rng.uniform(2,6),seed=950+i+off,hc_factor=hc)
    lab,P=detect(z,DX,flow_az=az,half_frac=hf)
    th=tophat_relief(z,DX)
    r=object_shuffle_test(th,lab,np.ones_like(lab,bool),DX,nsim=39,seed=i)
    if r: pq.append(r['p_q']); pp.append(r['p_pk']); fill.append(r['fill'])
pq=np.array(pq);pp=np.array(pp)
print(f"hf={hf} {pl} jit={jit}: n={len(pq)} p_q<.05 {np.mean(pq<0.05):.2f} | p_pk<.05 {np.mean(pp<0.05):.2f} | fill {np.mean(fill):.2f}",flush=True)
