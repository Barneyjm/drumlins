import sys, json, base64, io, numpy as np, pandas as pd
from scipy import ndimage as ndi
from PIL import Image
sys.path.insert(0,'.')
from candidates import load
from train import add_context
DX=20.0; R=90; S=3
allc=pd.read_csv('candidates_ctx.csv')

samp=set(pd.read_csv('label_sample.csv').cid)
a=allc[~allc.cid.isin(samp)]
yes=a[(a.strict==1)&a.height_m.between(10,25)&a.elong.between(2,4)&(a.az_dev<8)&(a.nb_coherence>0.7)&(a.nb_count>=12)&(a.slope_max<12)]
yes=yes.sort_values('nb_coherence',ascending=False)
# spread picks geographically
pick_y=[]; 
for _,r in yes.iterrows():
    if all(np.hypot(r.x-p.x,r.y-p.y)>8000 for p in pick_y): pick_y.append(r)
    if len(pick_y)==4: break
no_valley=a[(a.slope_mean>9)&(a.nb_coherence<0.4)&a.height_m.between(8,40)].sample(1,random_state=3)
no_ridge=a[(a.height_m>60)].sample(1,random_state=4)
no_lowbump=a[(a.height_m<4.5)&(a.nb_coherence<0.35)&(a.slope_mean<3)].sample(1,random_state=5)
no_cross=a[(a.az_dev>55)&(a.elong>2)&(a.nb_coherence>0.7)&a.height_m.between(6,20)].sample(1,random_state=6)
zf,valid,tr=load(); H,W=zf.shape
zs=ndi.gaussian_filter(zf,0.6); gy,gx=np.gradient(zs,DX); hs=np.zeros_like(zs)
sl=np.arctan(np.hypot(gx,gy)*6.0); asp=np.arctan2(-gx,gy); alt=np.radians(40)
for az_l,w in ((315,0.5),(45,0.25),(225,0.25)):
    aa=np.radians(az_l); hs+=w*(np.sin(alt)*np.cos(sl)+np.cos(alt)*np.sin(sl)*np.cos(aa-asp))
def chip(p):
    r0,c0=int(p.row),int(p.col); ra,rb=max(r0-R,0),min(r0+R,H); ca,cb=max(c0-R,0),min(c0+R,W)
    h=hs[ra:rb,ca:cb]; lo,hi=np.percentile(h,[1,99]); h=np.clip((h-lo)/(hi-lo+1e-9),0,1)
    g=(h*255).astype(np.uint8); rgb=np.stack([g]*3,-1); wat=~valid[ra:rb,ca:cb]
    rgb[wat]=(rgb[wat]*0.35+np.array([70,120,190])*0.65).astype(np.uint8)
    im=Image.fromarray(rgb).resize(((cb-ca)*S//2*2,(rb-ra)*S//2*2),Image.BICUBIC)
    # small orange ring at the candidate
    ar=np.array(im); cy,cx=(r0-ra)*im.height/(rb-ra),(c0-ca)*im.width/(cb-ca)
    yy,xx=np.mgrid[0:ar.shape[0],0:ar.shape[1]]; d=np.hypot(yy-cy,xx-cx); ar[(d>22)&(d<26)]=(255,150,0)
    im=Image.fromarray(ar).resize((300,300),Image.LANCZOS)
    b=io.BytesIO(); im.save(b,'JPEG',quality=78); return 'data:image/jpeg;base64,'+base64.b64encode(b.getvalue()).decode()
ex=[]
caps_y=["Classic: smooth oval hill, low ground all round, neighbours point the same way",
        "Herd: many similar hills, all parallel. The ringed one is a drumlin",
        "Teardrop: blunt end facing up-ice, tapering tail",
        "Long and slim drumlins still count"]
for p,cap in zip(pick_y,caps_y): ex.append(dict(kind='yes',cap=cap,img=chip(p)))
for d,cap in ((no_valley,"Not: a bump on a valley side. No low ground on the uphill side"),
              (no_ridge,"Not: part of a big hillside or upland, far too large and attached"),
              (no_lowbump,"Not: a faint lump on flat ground. No clear hill shape"),
              (no_cross,"Not: elongated, but across the grain of the herd around it")):
    ex.append(dict(kind='no',cap=cap,img=chip(d.iloc[0])))
json.dump(ex,open('label_app/examples.json','w'))
print(len(pick_y),'yes picks', [ (int(p.cid),round(p.height_m,1)) for p in pick_y])
# preview grid
ims=[Image.open(io.BytesIO(base64.b64decode(e['img'].split(',')[1]))) for e in ex]
g=Image.new('RGB',(1200,600),'white')
for k,im in enumerate(ims): g.paste(im,((k%4)*300,(k//4)*300))
g.save('examples_preview.jpg')
