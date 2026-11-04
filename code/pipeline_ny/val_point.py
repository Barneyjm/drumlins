import sys, time, numpy as np
sys.path.insert(0,'.')
from spectral import synthetic_field
from detect import detect
from pointtest import conditional_test
N,DX=500,20.0
res={}
t=time.time()
for pl,jit in (("lattice",0.18),("lattice",0.28),("hardcore",0.0),("poisson",0.0)):
    ps=[];zs=[];fills=[]
    for i in range(20):
        rng=np.random.default_rng(900+i); lat=rng.uniform(300,700); az=rng.uniform(0,180)
        z=synthetic_field(N,DX,lat_spacing=lat,long_spacing=3*lat,flow_az=az,width=0.5*lat,elong=3,height=12,
              placement=pl,jitter=jit,noise_amp=rng.uniform(2,6),seed=950+i)
        lab,P=detect(z,DX,flow_az=az)
        r=conditional_test(lab,np.ones_like(lab,bool),DX,nsim=49,seed=i)
        if r: ps.append(r['p_regular']); zs.append(r['z']); fills.append(r['fill'])
    ps=np.array(ps)
    print(f"{pl:8s} jit={jit}: n={len(ps)}  frac p<0.05 {np.mean(ps<0.05):.2f}  median z {np.median(zs):.2f}  fill {np.mean(fills):.2f}")
print(f"{time.time()-t:.0f}s")
