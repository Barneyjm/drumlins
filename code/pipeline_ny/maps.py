import numpy as np, pandas as pd, rasterio, matplotlib
matplotlib.use('Agg'); import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
from scipy import ndimage as ndi
with rasterio.open('data/ny_dem_20m.tif') as s:
    z=s.read(1); water=s.read(2)>0.5; tr=s.transform
d=pd.read_csv('ny_windows.csv'); qthr,_=np.load('data/null_thr.npy')
zz=np.where(np.isfinite(z),z,np.nanmean(z))
res=zz-ndi.gaussian_filter(zz,60)   # ~1.2 km high-pass for display
gy,gx=np.gradient(ndi.gaussian_filter(zz,1),20)
hs=np.clip(0.6+ (-gx*np.cos(np.radians(315))+gy*np.sin(np.radians(315)))*3,0,1)
ext=[tr.c, tr.c+tr.a*z.shape[1], tr.f+tr.e*z.shape[0], tr.f]
def base(ax):
    ax.imshow(np.ma.masked_where(water,hs),cmap='gray',extent=ext,vmin=0,vmax=1.2)
    ax.imshow(np.ma.masked_where(~water,water),cmap='Blues',extent=ext,vmin=0,vmax=1.5,alpha=.6)
    ax.set_xticks([]);ax.set_yticks([])
g=d[d.anisotropy>0.7]
L=2500
segs=[[(x-L*np.sin(np.radians(a)),y-L*np.cos(np.radians(a))),(x+L*np.sin(np.radians(a)),y+L*np.cos(np.radians(a)))] for x,y,a in zip(g.x,g.y,g.flow_az)]
fig,axs=plt.subplots(2,1,figsize=(11,14),dpi=110)
base(axs[0])
lc=LineCollection(segs,array=g.lam_lat.clip(200,900),cmap='viridis',linewidths=2.6)
axs[0].add_collection(lc); fig.colorbar(lc,ax=axs[0],shrink=.6,label='lateral spacing (m)')
axs[0].set_title('Ice-flow direction (line orientation) and lateral drumlin spacing\n15 km windows, anisotropy > 0.7',fontsize=11)
base(axs[1])
sig=g.q_lat.fillna(0)>qthr
sc=axs[1].scatter(g.x,g.y,c=g.q_lat.fillna(0).clip(0,5),cmap='magma',s=np.where(sig,70,18),edgecolors=np.where(sig,'w','none'))
fig.colorbar(sc,ax=axs[1],shrink=.6,label='spectral peak sharpness Q (lateral)')
axs[1].set_title(f'Pattern regularity: white-ringed = Q above random-placement 95th pct ({qthr:.2f})',fontsize=11)
plt.tight_layout(); plt.savefig('ny_drumlin_maps.png')
# zoom on residual relief, a strong window
best=g.sort_values('pk_lat').iloc[-1]; r,c=int(best.row),int(best.col)
fig2,ax=plt.subplots(figsize=(7,7),dpi=110)
ax.imshow(res[r:r+768,c:c+768],cmap='RdBu_r',vmin=-15,vmax=15); ax.set_xticks([]);ax.set_yticks([])
ax.set_title(f'Residual relief, strongest window: flow {best.flow_az:.0f}°, lateral λ {best.lam_lat:.0f} m, Q {best.q_lat:.1f}',fontsize=10)
plt.savefig('ny_zoom.png')
# west/centre/east orientation summary
xs=g.x; t1,t2=np.percentile(xs,[33,67])
for nm,m in (('west',xs<t1),('centre',(xs>=t1)&(xs<t2)),('east',xs>=t2)):
    a=np.radians(2*g.flow_az[m]); mean=(np.degrees(np.arctan2(np.sin(a).mean(),np.cos(a).mean()))/2)%180
    print(f"{nm}: n={m.sum()} mean flow axis {mean:.0f} deg, median lateral spacing {g.lam_lat[m].median():.0f} m")
