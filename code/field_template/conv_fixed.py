import sys, numpy as np, pandas as pd
THR=sys.argv[1]; PATH=float(sys.argv[2]) if len(sys.argv)>2 else 20000
f=np.load(f'flowfield_4km_{THR}.npz'); fx,fy,dens,coh=f['fx'],f['fy'],f['dens'],f['coh']
G=1000.0; x0=float(f['x0']); y1=float(f['y1']); ny,nx=fx.shape; mask=dens>=8
div=np.gradient(fx,G,axis=1)-np.gradient(fy,G,axis=0)
t=pd.read_csv(f'tile_morph_{THR}.csv'); rows=[]
for _,r in t.iterrows():
    yy,xx=(y1-r.y)/G,(r.x-x0)/G; acc=0; s=0; ok=True
    while s<PATH:
        i,j=int(round(yy)),int(round(xx))
        if not(0<=i<ny and 0<=j<nx) or not mask[i,j]: ok=False; break
        acc+=div[i,j]*500; xx-=fx[i,j]*0.5; yy+=fy[i,j]*0.5; s+=500
    if ok:
        i,j=int((y1-r.y)/G),int((r.x-x0)/G)
        rows.append(dict(tile=r.tile,conv=-acc,coh=coh[i,j],x=r.x,y=r.y))
d=pd.DataFrame(rows); d.to_csv(f'tile_conv_{THR}_{int(PATH/1000)}km.csv',index=False); print(THR,PATH/1000,'km:',len(d),'tiles')
