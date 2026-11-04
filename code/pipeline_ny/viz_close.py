import json,sys,numpy as np,pandas as pd
from scipy import ndimage as ndi
from scipy.spatial import cKDTree
from PIL import Image
sys.path.insert(0,'.')
from candidates import load
from detect import detect
lab=json.load(open('labels_round1.json'))
orig=pd.read_csv('candidates_ctx.csv'); new=pd.read_csv('candidates_ctx_closed3.csv')
L=orig[orig.cid.astype(str).isin(lab)].copy(); L['label']=L.cid.astype(str).map(lab)
d,_=cKDTree(new[['x','y']].values).query(L[['x','y']].values); L['d']=d
um=L[(L.d>=150)&(L.label=='yes')].head(4)
zf,valid,tr=load(); H,W=zf.shape; DX=20.0; R=60
zs=ndi.gaussian_filter(zf,0.6); gy,gx=np.gradient(zs,DX)
sl=np.arctan(np.hypot(gx,gy)*6); asp=np.arctan2(-gx,gy); a=np.radians(315); alt=np.radians(40)
hs=np.sin(alt)*np.cos(sl)+np.cos(alt)*np.sin(sl)*np.cos(a-asp)
tiles=[]
for _,p in um.iterrows():
    r0,c0=int(p.row),int(p.col); ra,rb=r0-R,r0+R; ca,cb=c0-R,c0+R
    h=hs[ra:rb,ca:cb]; lo,hi=np.percentile(h,[1,99]); g=(np.clip((h-lo)/(hi-lo),0,1)*255).astype(np.uint8)
    rgb=np.stack([g]*3,-1)
    for pre,col in ((0,(255,150,0)),(3,(0,200,255))):
        labm,P=detect(zf[ra:rb,ca:cb],DX,valid=valid[ra:rb,ca:cb],flow_az=None,h_thresh=1.5,h_split=1.5,h_peak=3.0,min_area=0.005e6,max_area=5e6,min_elong=0.0,pre_close_px=pre)
        e=(labm>0)&~ndi.binary_erosion(labm>0)
        rgb[e]=col
    rgb[R-1:R+2,R-1:R+2]=(255,0,255)
    tiles.append(Image.fromarray(rgb).resize((360,360),Image.NEAREST))
out=Image.new('RGB',(720,720))
for k,t in enumerate(tiles): out.paste(t,((k%2)*360,(k//2)*360))
out.save('close_compare.png')
