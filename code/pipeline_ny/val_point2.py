import sys, numpy as np
sys.path.insert(0,'.')
from spectral import synthetic_field
from detect import detect
from pointtest import conditional_test
N,DX=500,20.0
hf=float(sys.argv[1]); ns=int(sys.argv[2]) if len(sys.argv)>2 else 30
for pl,jit in (("lattice",0.18),("hardcore",0.0)):
    ps=[];zs=[]
    for i in range(ns):
        rng=np.random.default_rng(900+i); lat=rng.uniform(300,700); az=rng.uniform(0,180)
        z=synthetic_field(N,DX,lat_spacing=lat,long_spacing=3*lat,flow_az=az,width=0.5*lat,elong=3,height=12,
              placement=pl,jitter=jit,noise_amp=rng.uniform(2,6),seed=950+i)
        lab,P=detect(z,DX,flow_az=az,half_frac=hf)
        r=conditional_test(lab,np.ones_like(lab,bool),DX,nsim=39,seed=i)
        if r: ps.append(r['p_regular']); zs.append(r['z'])
    ps=np.array(ps)
    print(f"half_frac={hf} {pl:8s}: n={len(ps)} frac p<0.05 {np.mean(ps<0.05):.2f}  median z {np.median(zs):.2f}")
