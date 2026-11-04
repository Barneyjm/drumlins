import json, numpy as np, pandas as pd
from scipy.spatial import cKDTree
from sklearn.ensemble import HistGradientBoostingClassifier
from train import FEATS
lab=json.load(open('labels_round1.json'))
orig=pd.read_csv('candidates_ctx.csv'); new=pd.read_csv('candidates_ctx_closed3.csv')
L=orig[orig.cid.astype(str).isin(lab)].copy(); L['label']=L.cid.astype(str).map(lab)
d,i=cKDTree(new[['x','y']].values).query(L[['x','y']].values)
L=L[d<150].assign(nidx=i[d<150])
T=L[L.label.isin(['yes','no'])&(L.height_m<60)].drop_duplicates('nidx')
X=new.iloc[T.nidx.values][FEATS].values; y=(T.label=='yes').astype(int).values
clf=HistGradientBoostingClassifier(max_depth=3,learning_rate=0.06,max_iter=300,l2_regularization=1.0,min_samples_leaf=8).fit(X,y)
new['p']=clf.predict_proba(new[FEATS].values)[:,1]
used=set(L.nidx)  # anything already labelled (incl. unsure)
pool=new[~new.index.isin(used)&(new.height_m<60)].copy()
def thin(df,k,mind=1500):
    out=[]; pts=[]
    for idx,r in df.iterrows():
        if all(np.hypot(r.x-a,r.y-b)>mind for a,b in pts):
            out.append(idx); pts.append((r.x,r.y))
        if len(out)==k: break
    return out
unc=pool.assign(u=abs(pool.p-0.5)).sort_values('u')
unc=unc[unc.u<0.25]
pick_u=thin(unc.sample(frac=1,random_state=1).sort_values('u'),80)
rest=pool.drop(pick_u)
rnd=rest[(rest.elong<1.7)&rest.height_m.between(5,30)&(rest.nb_coherence>0.6)&(rest.nb_count>=8)]
pick_r=thin(rnd[rnd.p>=0.5].sample(frac=1,random_state=2),20,1200)+thin(rnd[rnd.p<0.5].sample(frac=1,random_state=3),20,1200)
S=new.loc[pick_u+pick_r].copy(); S['why']=['uncertain']*len(pick_u)+['rounded']*(len(S)-len(pick_u))
S=S.sample(frac=1,random_state=9)
S['rid']=['r2_'+str(int(c)) for c in S.cid]
S.to_csv('label_sample_r2.csv',index=False)
print(len(S),S.why.value_counts().to_dict(),'p range',S.p.min().round(2),S.p.max().round(2))
print('rounded pool size',len(rnd),' model accepts',(rnd.p>=.5).mean().round(2),'of them; vs all herd members',(pool[(pool.nb_coherence>0.6)&(pool.nb_count>=8)].p>=.5).mean().round(2))
