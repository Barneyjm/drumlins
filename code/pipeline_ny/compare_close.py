import json, numpy as np, pandas as pd
from scipy.spatial import cKDTree
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.model_selection import StratifiedKFold, cross_val_predict
from sklearn.metrics import roc_auc_score, average_precision_score, precision_recall_fscore_support
from train import add_context, FEATS
lab=json.load(open('labels_round1.json'))
orig=pd.read_csv('candidates_ctx.csv'); new=add_context(pd.read_csv('candidates_all_closed3.csv'))
new.to_csv('candidates_ctx_closed3.csv',index=False)
L=orig[orig.cid.astype(str).isin(lab)].copy(); L['label']=L.cid.astype(str).map(lab)
# map each labelled original to the nearest new candidate within 150 m
d,i=cKDTree(new[['x','y']].values).query(L[['x','y']].values)
L['new_idx']=np.where(d<150,i,-1)
print('labelled originals matched to a closed-cut candidate:',(L.new_idx>=0).mean().round(2))
# fragments: originals that now share one new candidate
shared=L[L.new_idx>=0].groupby('new_idx').size()
print('new candidates absorbing >1 labelled original:',int((shared>1).sum()))
def cv(df,y,name):
    clf=HistGradientBoostingClassifier(max_depth=3,learning_rate=0.06,max_iter=300,l2_regularization=1.0,min_samples_leaf=8)
    aucs=[];prs=[];f1s=[]
    for seed in range(5):
        p=cross_val_predict(clf,df[FEATS].values,y,cv=StratifiedKFold(5,shuffle=True,random_state=seed),method='predict_proba')[:,1]
        aucs.append(roc_auc_score(y,p)); prs.append(average_precision_score(y,p))
        f1s.append(precision_recall_fscore_support(y,p>=0.5,average='binary',zero_division=0)[2])
    print(f"{name:22s} ROC-AUC {np.mean(aucs):.3f}  PR-AUC {np.mean(prs):.3f}  F1 {np.mean(f1s):.3f}  (n={len(y)})")
# same labelled set (only those matched, yes/no, h<60) for a fair comparison
M=L[(L.new_idx>=0)&L.label.isin(['yes','no'])&(L.height_m<60)].drop_duplicates('new_idx')
y=(M.label=='yes').astype(int).values
cv(M,y,'original candidates')
N=new.iloc[M.new_idx.values].reset_index(drop=True)
cv(N,y,'road-cuts filled')
# geometry change for yes-labelled drumlins
Y=M.label.values=='yes'
print(f"yes drumlins: median length {M.length_m.values[Y].mean():.0f} -> {N.length_m.values[Y].mean():.0f} m (mean); "
      f"median area {np.median(M.area_m2.values[Y])/1e3:.0f} -> {np.median(N.area_m2.values[Y])/1e3:.0f} thousand m2")
