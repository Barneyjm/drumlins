import sys, json, os, numpy as np, pandas as pd
from scipy import ndimage as ndi
from PIL import Image, ImageDraw
sys.path.insert(0,'.')
from candidates import load
from detect import detect
DX=20.0; R=100; S=3
zf,valid,tr=load(); H,W=zf.shape
samp=pd.read_csv('label_sample.csv')
zs=ndi.gaussian_filter(zf,0.6); gy,gx=np.gradient(zs,DX)
hs=np.zeros_like(zs)
sl=np.arctan(np.hypot(gx,gy)*6.0); asp=np.arctan2(-gx,gy); alt=np.radians(40)
for az_l,w in ((315,0.5),(45,0.25),(225,0.25)):
    a=np.radians(az_l); hs+=w*(np.sin(alt)*np.cos(sl)+np.cos(alt)*np.sin(sl)*np.cos(a-asp))
os.makedirs('label_app/chips',exist_ok=True)
for f in os.listdir('label_app/chips'): os.remove('label_app/chips/'+f)
items=[]
for _,p in samp.iterrows():
    r0,c0=int(p.row),int(p.col)
    ra,rb=max(r0-R,0),min(r0+R,H); ca,cb=max(c0-R,0),min(c0+R,W)
    h=hs[ra:rb,ca:cb]; lo,hi=np.percentile(h,[1,99]); h=np.clip((h-lo)/(hi-lo+1e-9),0,1)
    g=(h*255).astype(np.uint8); rgb=np.stack([g]*3,-1)
    wat=~valid[ra:rb,ca:cb]; rgb[wat]=(rgb[wat]*0.35+np.array([70,120,190])*0.65).astype(np.uint8)
    img=Image.fromarray(rgb).resize(((cb-ca)*S,(rb-ra)*S),Image.BICUBIC)
    d=ImageDraw.Draw(img); d.rectangle([12,img.height-20,12+50*S,img.height-14],fill=(255,255,255)); 
    img.save(f'label_app/chips/{int(p.cid)}_c.jpg',quality=82)
    lab,P=detect(zf[ra:rb,ca:cb],DX,valid=valid[ra:rb,ca:cb],flow_az=None,h_thresh=1.5,h_split=1.5,h_peak=3.0,min_area=0.005e6,max_area=5e6,min_elong=0.0)
    best=None
    for q in P:
        dd=(q['row']+ra-p.row)**2+(q['col']+ca-p.col)**2
        if best is None or dd<best[0]: best=(dd,q['label'])
    if best is not None and best[0]<9:
        m=lab==best[1]; mb=np.array(Image.fromarray(m.astype(np.uint8)*255).resize(img.size,Image.NEAREST))>0
        edge=mb&~ndi.binary_erosion(mb,iterations=2)
        a=np.array(img); a[edge]=(255,150,0); img=Image.fromarray(a)
    img.save(f'label_app/chips/{int(p.cid)}_o.jpg',quality=82)
    items.append(dict(cid=int(p.cid),h=round(float(p.height_m),1),L=int(p.length_m),W=int(p.width_m)))
json.dump(items,open('label_app/items.json','w'))
ims=[Image.open(f'label_app/chips/{i["cid"]}_{s}.jpg').resize((340,340)) for i in items[:3] for s in 'co']
out=Image.new('RGB',(340*2,340*3),'white')
for k,im in enumerate(ims): out.paste(im,((k%2)*340,(k//2)*340))
out.save('chips_preview.jpg'); print(len(items))
