import numpy as np, pandas as pd, rasterio, matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
from pyproj import Transformer
from scipy import ndimage as ndi
s=pd.read_csv('candidates_scored2.csv')
lon,lat=Transformer.from_crs('EPSG:32618','EPSG:4326',always_xy=True).transform(s.x.values,s.y.values); s['lon']=lon; s['lat']=lat
with rasterio.open('data/ny_dem_20m.tif') as f: z=f.read(1); water=f.read(2)>0.5; tr=f.transform
# distance to Lake Ontario (largest water body touching the north edge)
lab,_=ndi.label(water); ont=lab==lab[5,lab.shape[1]//2]
dist=ndi.distance_transform_edt(~ont)*20
s['d_ont_km']=dist[s.row.astype(int).clip(0,z.shape[0]-1),s.col.astype(int).clip(0,z.shape[1]-1)]/1000
regions={'north of Cayuga Lake':(s.lon.between(-76.9,-76.5)&s.lat.between(42.95,43.15)),
         'west of Oneida Lake':(s.lon.between(-76.35,-76.1)&s.lat.between(43.05,43.3)),
         'Lake Ontario shore (<8 km)':(s.d_ont_km<8),
         }
regions['rest of field']=~(regions['north of Cayuga Lake']|regions['west of Oneida Lake']|regions['Lake Ontario shore (<8 km)'])
def wmed(e,w):
    o=np.argsort(e); c=np.cumsum(w[o])/w.sum(); return e[o][np.searchsorted(c,.5)]
rows=[]
for nm,m in regions.items():
    g=s[m&(s.height_m<60)]
    rows.append(dict(region=nm, **{f'med@{t}':round(g.elong[g.p_drumlin>=t].median(),2) for t in (0.3,0.5,0.7)},
                     weighted=round(wmed(g.elong.values,g.p_drumlin.values),2), n_05=int((g.p_drumlin>=.5).sum())))
print(pd.DataFrame(rows).to_string(index=False))
# map: tile-level weighted median elongation
t=pd.read_csv('ny_tiles_r2.csv')
gy,gx=np.gradient(ndi.gaussian_filter(np.where(np.isfinite(z),z,np.nanmean(z)),1),20)
hs=np.clip(0.6+(-gx*0.707+gy*0.707)*3,0,1)
fig,ax=plt.subplots(figsize=(11,7.5),dpi=120)
ax.imshow(np.ma.masked_where(water,hs),cmap='gray',vmin=0,vmax=1.2)
ax.imshow(np.ma.masked_where(~water,water),cmap='Blues',vmin=0,vmax=1.5,alpha=.6)
from matplotlib.patches import Rectangle
cm=plt.cm.viridis; vmin,vmax=1.8,3.4
for _,r in t.dropna(subset=['elong_wmed']).iterrows():
    if r['n_0.5']<10: continue
    ax.add_patch(Rectangle((r.col,r.row),512,512,fc=cm((np.clip(r.elong_wmed,vmin,vmax)-vmin)/(vmax-vmin)),alpha=.55,ec='none'))
    ax.text(r.col+256,r.row+256,f"{r.elong_wmed:.1f}",ha='center',va='center',fontsize=7,color='w')
sm=plt.cm.ScalarMappable(cmap=cm,norm=plt.Normalize(vmin,vmax)); fig.colorbar(sm,ax=ax,shrink=.7,label='median drumlin elongation (length / width)')
for nm,(lo,la) in {'Cayuga L.':(-76.72,42.93),'Oneida L. →':(-76.2,43.2),'Seneca L.':(-76.95,42.75)}.items():
    xx,yy=Transformer.from_crs('EPSG:4326','EPSG:32618',always_xy=True).transform(lo,la); cc,rr=~tr*(xx,yy)
    ax.text(cc,rr,nm,color='k',fontsize=9,weight='bold',ha='center',bbox=dict(fc='w',alpha=.6,lw=0,pad=1))
ax.set_title('Drumlin elongation across the New York field (model drumlins, probability-weighted median per 10 km tile)',fontsize=10)
ax.set_xticks([]);ax.set_yticks([]); plt.tight_layout(); plt.savefig('elongation_map.png')
