import sys,numpy as np,pandas as pd,rasterio,matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from scipy import ndimage as ndi
sys.path.insert(0,'.')
from detect import detect, tophat_relief
with rasterio.open('data/ny_dem_20m.tif') as s: z=s.read(1); water=s.read(2)>0.5; tr=s.transform
t=pd.read_csv('ny_tiles_shuffle.csv'); t=t[t.skipped==0]
zz=np.where(np.isfinite(z),z,np.nanmean(z)); gy,gx=np.gradient(ndi.gaussian_filter(zz,1),20)
hs=np.clip(0.6+(-gx*0.707+gy*0.707)*3,0,1)
fig,axs=plt.subplots(2,1,figsize=(11,14),dpi=110)
ax=axs[0]; ax.imshow(np.ma.masked_where(water,hs),cmap='gray',vmin=0,vmax=1.2)
ax.imshow(np.ma.masked_where(~water,water),cmap='Blues',vmin=0,vmax=1.5,alpha=.6)
ratio=(t.pk_obs/t.pk_null_med).clip(0.5,2)
cm=plt.cm.coolwarm
for _,r in t.iterrows():
    v=(np.clip(r.pk_obs/r.pk_null_med,0.5,2)-0.5)/1.5
    ax.add_patch(Rectangle((r.col,r.row),512,512,fc=cm(v),alpha=.45,ec='k' if r.p_pk<0.05 else 'none',lw=2.2))
    ax.text(r.col+256,r.row+256,f"{int(r.n)}",ha='center',va='center',fontsize=7)
sm=plt.cm.ScalarMappable(cmap=cm,norm=plt.Normalize(0.5,2)); fig.colorbar(sm,ax=ax,shrink=.6,label='spectral peak: real / shuffled median')
ax.set_title('Real drumlin arrangement vs. same drumlins shuffled (no overlap, same patch)\nblack outline = more regular than shuffles (p<0.05); number = drumlins detected',fontsize=10)
ax.set_xticks([]);ax.set_yticks([])
# detection sample: tile with most drumlins
b=t.sort_values('n').iloc[-1]; r0,c0=int(b.row),int(b.col)
sub=np.where(np.isfinite(z[r0:r0+512,c0:c0+512]),z[r0:r0+512,c0:c0+512],np.nanmean(z))
lab,P=detect(sub,20.0,flow_az=b.flow_in,half_frac=0.5)
th=tophat_relief(sub,20.0)
axs[1].imshow(th,cmap='Greys_r',vmin=0,vmax=25)
axs[1].contour(lab>0,levels=[0.5],colors='orange',linewidths=0.8)
axs[1].set_title(f'Detected drumlin footprints (orange), densest tile: {len(P)} drumlins, p={b.p_pk:.2f}',fontsize=10)
axs[1].set_xticks([]);axs[1].set_yticks([])
plt.tight_layout(); plt.savefig('ny_shuffle_test.png')
from scipy.stats import binom
print('P(>=9 of 68 | p=.08) =',round(1-binom.cdf(8,68,0.08),3),' | P(>=9|p=.05)=',round(1-binom.cdf(8,68,0.05),3))
