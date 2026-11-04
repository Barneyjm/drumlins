import numpy as np, pandas as pd, statsmodels.formula.api as smf
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
from matplotlib.patches import Ellipse, FancyBboxPatch, FancyArrowPatch
OUT='/home/claude/drumlin-site/docs/assets/'
ICE='#2f7fc1'; TILL='#c08a3e'; INK='#2b2f33'; MUTE='#6b737b'; RED='#d1495b'; GRN='#2e9e6b'
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'text.color':INK,'axes.edgecolor':MUTE,'axes.labelcolor':INK,'xtick.color':MUTE,'ytick.color':MUTE,'svg.fonttype':'none'})
def save(fig,name): fig.savefig(OUT+name,format='svg',facecolor='white',bbox_inches='tight',pad_inches=0.15); plt.close(fig)
def drum(ax,x,y,L,W,ang=90,fc=TILL,ec='#8a5f22',lw=0.8,alpha=1):
    ax.add_patch(Ellipse((x,y),L,W,angle=ang,fc=fc,ec=ec,lw=lw,alpha=alpha))
def arrow(ax,x0,y0,x1,y1,c=ICE,lw=2,ms=14):
    ax.add_patch(FancyArrowPatch((x0,y0),(x1,y1),arrowstyle='-|>',mutation_scale=ms,color=c,lw=lw))

# 1. one method across many fields
fig,ax=plt.subplots(figsize=(8.6,2.2)); ax.set_xlim(0,12); ax.set_ylim(0,3); ax.axis('off')
steps=[('16 fields','3 continents'),('Elevation','lidar, 3DEP, 30 m'),('Detector','same settings'),('Classifier','one pooled model'),('Blind check','48 cards / field'),('Shapes','L, W, elongation')]
xs=np.linspace(0.95,11.05,len(steps))
for i,(t,s) in enumerate(steps):
    c = ICE if i in (2,3,4) else MUTE
    ax.add_patch(FancyBboxPatch((xs[i]-0.82,1.15),1.64,1.15,boxstyle='round,pad=0.02,rounding_size=0.12',fc='white',ec=c,lw=1.6))
    ax.text(xs[i],1.82,t,ha='center',va='center',fontsize=9.5,weight='bold',color=INK)
    ax.text(xs[i],1.36,s,ha='center',va='center',fontsize=7.2,color=MUTE)
    if i<len(steps)-1: arrow(ax,xs[i]+0.84,1.72,xs[i+1]-0.84,1.72,c=MUTE,lw=1.2,ms=10)
ax.text(xs[3],0.45,'identical in every field, so differences between fields\nare not differences in mapping style',ha='center',fontsize=8.5,color=ICE)
ax.plot([xs[2]-0.82,xs[4]+0.82],[0.92,0.92],color=ICE,lw=1.2)
save(fig,'new_method.svg')

# 2. margin gradient (real bin means from the margin chart)
bins=['0–10','10–20','20–30','30–45','45–60','60–100','100–150','150–250']
pct=[-15.5,-8.2,-3.5,-4.5,8.1,6.6,0.2,-0.2]
fig,ax=plt.subplots(figsize=(7.5,2.6)); ax.set_xlim(-0.6,8.9); ax.set_ylim(-1.3,2.4); ax.axis('off')
ax.add_patch(plt.Rectangle((-0.6,-0.55),0.35,2.6,fc='#dbe9f6',ec='none'))
ax.plot([-0.25,-0.25],[-0.55,2.05],color=ICE,lw=2.5); ax.text(-0.42,-0.75,'ice\nlimit',ha='center',va='top',fontsize=8,color=ICE)
E0=2.6; W=0.30; EX=3
for i,(b,p) in enumerate(zip(bins,pct)):
    x=i+0.35; E=E0*(1+EX*p/100); L=W*E
    for y in (0.15,1.25): drum(ax,x,y,L,W,ang=0,alpha=1 if i<5 else 0.45)
    ax.text(x,-0.75,b,ha='center',fontsize=8,color=MUTE)
    ax.text(x,1.82,f'{p:+.0f}%',ha='center',fontsize=9,weight='bold',color=RED if p<0 and i<5 else (MUTE if i>=5 else GRN))
ax.text(3.9,-1.2,'distance inside the ice limit (km)  →  ice-sheet interior',ha='center',fontsize=8.5,color=MUTE)
ax.plot([4.85,4.85],[-0.5,2.0],ls='--',color=MUTE,lw=0.8); ax.text(4.95,2.12,'60 km: effect fades',fontsize=8,color=MUTE)
arrow(ax,8.75,0.7,7.9,0.7); ax.text(8.75,0.9,'ice flow',ha='right',fontsize=8,color=ICE)
ax.text(-0.6,2.42,'Elongation relative to the field average (shape differences exaggerated 3×)',fontsize=8.5,color=INK,va='bottom')
save(fig,'new_margin.svg')

# 3. theory vs observation for speed
fig,axs=plt.subplots(1,2,figsize=(7.5,2.6))
for ax,title,obs in zip(axs,['Theory predicts','We observe'],[False,True]):
    ax.set_xlim(0,5); ax.set_ylim(0,3.2); ax.axis('off')
    ax.text(2.5,3.05,title,ha='center',fontsize=11,weight='bold',color=RED if not obs else GRN)
    # slow ice (left) and fast/converging ice (right)
    ax.text(1.1,2.55,'slower ice',ha='center',fontsize=8.5,color=MUTE); ax.text(3.9,2.55,'faster, converging ice',ha='center',fontsize=8.5,color=MUTE)
    arrow(ax,1.1,2.35,1.1,1.95,lw=1.5,ms=11); arrow(ax,3.9,2.35,3.9,1.95,lw=3,ms=16)
    drum(ax,1.1,1.0,1.0,0.36,ang=90)
    if obs: drum(ax,3.9,1.0,1.55,0.36,ang=90); txt='longer: elongation rises'
    else: drum(ax,3.9,1.0,1.2,0.62,ang=90); txt='bigger but stubbier'
    ax.text(3.9,0.08,txt,ha='center',fontsize=8.5,color=INK)
    ax.text(1.1,0.08,'reference shape',ha='center',fontsize=8.5,color=INK)
fig.text(0.5,-0.04,'Observed in New York, Green Bay and Puget: converging flow lengthens drumlins (+0.4 to +0.9 in log elongation per unit convergence)',ha='center',fontsize=8,color=MUTE)
save(fig,'new_speed.svg')

# 4. cumulative slip: per-field slopes vs pooled (real fits)
a=pd.read_csv('/home/claude/cumslip.csv'); a=a[a.S05>0].copy(); a['lS']=np.log(a.S05); a['lE']=np.log(a.elong)
pooled=smf.ols('lE ~ C(field) + lS',a).fit().params['lS']
names={'NY':'Central New York','GB':'Green Bay','PS':'Puget','LG':'Langlade','AC':'Antrim–Charlevoix','PZ':'Pierz','TM':'Toimi','BR':'Branch Co.'}
rows=[]
for f,g in a.groupby('field'):
    m=smf.ols('lE ~ lS',g).fit(); rows.append((names[f],m.params['lS'],m.bse['lS'],len(g)))
rows=sorted(rows,key=lambda r:r[1])
fig,ax=plt.subplots(figsize=(7.5,3.0))
for k,(nm,b,se,n) in enumerate(rows):
    c=ICE if nm=='Green Bay' else TILL
    ax.plot([b-2*se,b+2*se],[k,k],color=c,lw=1.6); ax.plot(b,k,'o',color=c,ms=7)
    ax.text(-3.55,k,f'{nm} (n={n:,})',ha='right',va='center',fontsize=8,color=INK)
ax.axvline(0,color='#bbb',lw=0.9); ax.axvline(pooled,color=INK,ls='--',lw=1.4)
ax.text(pooled+0.05,len(rows)-0.35,f'pooled {pooled:+.2f}',fontsize=8.5,va='bottom')
ax.text(0.33,rows.index([r for r in rows if r[0]=='Green Bay'][0])-0.42,'Green Bay matches Zoet et al. (2021)',fontsize=7.5,color=ICE,va='top')
ax.set_xlim(-3.5,1.6); ax.set_ylim(-0.7,len(rows)+0.2); ax.set_yticks([])
ax.set_xlabel('slope of log elongation on log cumulative slip (dot = fit, bar = ±2 SE)')
ax.spines[['top','right','left']].set_visible(False)
save(fig,'new_slip.svg'); print('pooled',pooled)

# 5. width fixed, length varies (real field medians, to scale)
F=[('Menominee',716,184),('Chippewa',1205,327),('Peterborough',820,219),('Toimi',1111,327),('Pierz',841,242),('Leelanau',691,210),('Magellan–Otway',667,199),('Langlade',818,254),('Antrim–Charlevoix',793,237),('Puget',922,279),('Washington Co.',624,208),('Green Bay',628,210),('Central NY',651,216),('Vale of Eden',708,244),('Branch Co.',771,273),('Cavan–Monaghan',543,230)]
F=sorted(F,key=lambda r:r[1])
sp=430; n=len(F)
fig,ax=plt.subplots(figsize=(7.8,3.4)); ax.set_aspect('equal'); ax.axis('off')
ax.set_xlim(-sp*0.8,(n-1)*sp+sp*0.8); ax.set_ylim(-1500,1250)
for i,(nm,L,W) in enumerate(F):
    ax.add_patch(Ellipse((i*sp,0),W,L,fc=TILL,ec='#8a5f22',lw=0.8))
    ax.text(i*sp+60,-650,nm,rotation=60,ha='right',va='top',fontsize=7.5,color=MUTE)
ax.plot([-sp*0.6,(n-1)*sp+sp*0.6],[-620,-620],color='#ddd',lw=0.8)
ax.text(-sp*0.75,1200,'Median drumlin in each field, drawn to scale and sorted by length',fontsize=9,color=INK,va='top')
ax.text((n-1)*sp+sp*0.75,1200,'width 184–327 m (1.8×)\nlength 543–1,205 m (2.2×)',fontsize=8.5,color=ICE,ha='right',va='top')
x0=(n-1)*sp-500; ax.plot([x0,x0+500],[-1350,-1350],color=INK,lw=2); ax.text(x0+250,-1310,'500 m',ha='center',fontsize=7.5,va='bottom')
save(fig,'new_width.svg')
