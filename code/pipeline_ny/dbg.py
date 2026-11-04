import sys, numpy as np, matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
sys.path.insert(0,'.')
from spectral import synthetic_field
from detect import detect, tophat_relief
N,DX=512,20.0; lat=500; az=30
z,ctr=synthetic_field(N,DX,lat_spacing=lat,long_spacing=3*lat,flow_az=az,width=0.5*lat,elong=3,height=12,jitter=0.18,noise_amp=4,seed=401,return_centers=True)
lab,P=detect(z,DX,flow_az=az)
lab0,P0=detect(z,DX,flow_az=None,min_elong=0)
print('truth',len(ctr),'det',len(P),'det_nofilter',len(P0))
print('area med',np.median([p['area_m2'] for p in P0]),'elong med',np.median([p['length_m']/p['width_m'] for p in P0]))
th=tophat_relief(z,DX)
fig,ax=plt.subplots(1,2,figsize=(14,7))
ax[0].imshow(th,cmap='RdBu_r',vmin=-15,vmax=15); ax[0].plot(ctr[:,1],ctr[:,0],'k.',ms=4)
ax[1].imshow(lab>0,cmap='gray'); ax[1].plot([p['col'] for p in P],[p['row'] for p in P],'r.',ms=5); ax[1].plot(ctr[:,1],ctr[:,0],'c+',ms=5)
for a in ax: a.set_xlim(0,N); a.set_ylim(N,0)
plt.savefig('dbg.png',dpi=80)
