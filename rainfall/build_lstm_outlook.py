"""Produce an experimental three-year LSTM scenario using only Open-Meteo data."""
import datetime as dt
import json
import math
import runpy
from pathlib import Path

import numpy as np
import torch
from scipy.stats import theilslopes
from torch import nn
from torch.nn import functional as F

torch.set_num_threads(2)
env=runpy.run_path('lstm_open_meteo.py')
model=env['model']; normal=env['normal']; doy=env['doy']
old=env['IFS']; newer=json.loads(Path('data/ifs_12sites_2026_to_oct19.json').read_text())
era=env['ERA']
names=[r[0] for r in json.loads(Path('data/rainfall_analysis.json').read_text())['sites']]
dates=old[0]['daily']['time']+newer[0]['daily']['time']
rain=np.stack([np.array(a['daily']['rain_sum']+b['daily']['rain_sum'],dtype=float)
               for a,b in zip(old,newer)])
assert dates[-1]=='2026-10-19' and len(set(dates))==len(dates)
assert all(np.isfinite(rain[:,1:]).ravel())

def feature(site,s,previous):
    d=doy(s);ang=2*math.pi*d/366
    return [np.log1p(max(0,float(previous)))/4,float(previous>=1),
            math.sin(ang),math.cos(ang),math.sin(2*ang),math.cos(2*ang),
            float(normal[site,d,0]),float(normal[site,d,1])]

# Refit from the validated prototype on all observations available by 19 Oct 2026.
seqs=[]; ys=[]; ids=[]
for site in range(12):
    for start in range(2,len(dates),90):
        stop=min(start+90,len(dates))
        x=np.array([feature(site,dates[t],rain[site,t-1]) for t in range(start,stop)],dtype=np.float32)
        y=np.array(rain[site,start:stop],dtype=np.float32)
        if np.isfinite(x).all() and np.isfinite(y).all():
            seqs.append(torch.from_numpy(x));ys.append(torch.from_numpy(y));ids.append(site)
optim=torch.optim.AdamW(model.parameters(),lr=.0008,weight_decay=.02)
for epoch in range(6):
    model.train()
    for ix in torch.randperm(len(seqs)).split(20):
        groups={}
        for k in ix.tolist():groups.setdefault(len(seqs[k]),[]).append(k)
        for g in groups.values():
            x=torch.stack([seqs[k] for k in g]);y=torch.stack([ys[k] for k in g])
            logit,mu,_=model(x,torch.tensor([ids[k] for k in g]))
            loss=F.binary_cross_entropy_with_logits(logit,(y>=1).float())+.15*(mu-y*torch.log(mu)).mean()
            optim.zero_grad();loss.backward();nn.utils.clip_grad_norm_(model.parameters(),1.0);optim.step()
    print('refit epoch',epoch+1,flush=True)
model.eval()

# The ERA5 trend is deliberately separate from the LSTM. A trend in reanalysis
# is not an attribution of anthropogenic climate change.
season=lambda m: ('Winter' if m<=2 else 'Pre-monsoon' if m<=5 else 'Southwest monsoon' if m<=9 else 'Post-monsoon')
trend={}
for site in range(12):
    by={(y,s):0.0 for y in range(1991,2026) for s in ('Winter','Pre-monsoon','Southwest monsoon','Post-monsoon')}
    for day,v in zip(era[site]['daily']['time'],era[site]['daily']['rain_sum']):
        by[(int(day[:4]),season(int(day[5:7])))]+=v
    for s in ('Winter','Pre-monsoon','Southwest monsoon','Post-monsoon'):
        vals=[by[(y,s)] for y in range(1991,2026)]
        slope=theilslopes(vals,list(range(1991,2026))).slope
        trend[(site,s)]=[round(slope*10,2),round(float(np.mean(vals)),2)]

hist_bins=[[[] for _ in range(366)] for _ in range(12)]
for site in range(12):
    for t,s in enumerate(dates):
        if np.isfinite(rain[site,t]) and rain[site,t]>=1:
            hist_bins[site][doy(s)].append(rain[site,t])
wet_pools=[]
for site in range(12):
    wet_pools.append([np.array([v for shift in range(-15,16) for v in hist_bins[site][(d+shift)%366]],dtype=np.float32)
                      for d in range(366)])

future_start=dt.date(2026,10,20)
future_end=dt.date(2029,10,20)
future=[future_start+dt.timedelta(days=i) for i in range((future_end-future_start).days+1)]
members=256
ids=torch.arange(12).repeat_interleave(members)
gen=np.random.default_rng(379)
sim=np.repeat(rain[:,-1,None],members,axis=1).astype(np.float32)
h=None
rows=[]
with torch.no_grad():
    # Initial state is warmed solely with observed rainfall ending on 19 Oct 2026.
    for t in range(len(dates)-45,len(dates)):
        prev=np.repeat(rain[:,t-1,None],members,axis=1).reshape(-1)
        calendar=np.array([feature(i,dates[t],prev.reshape(12,members)[i,0]) for i in range(12)],dtype=np.float32)
        x=np.repeat(calendar,members,axis=0)
        _,_,h=model(torch.from_numpy(x)[:,None,:],ids,h)
    for day in future:
        s=day.isoformat();d=doy(s)
        prev=sim.reshape(-1)
        # Calendar and ERA5 normals are known in advance; each ensemble member
        # only sees its own simulated previous rain.
        calendar=np.array([feature(i,s,0)[2:] for i in range(12)],dtype=np.float32)
        x=np.concatenate([np.log1p(prev).reshape(-1,1)/4,(prev>=1).reshape(-1,1).astype(np.float32),
                          np.repeat(calendar,members,axis=0)],axis=1).astype(np.float32)
        logit,mean,h=model(torch.from_numpy(x)[:,None,:],ids,h)
        p=torch.sigmoid(logit[:,0]).numpy().reshape(12,members)
        mu=mean[:,0].numpy().reshape(12,members)
        wet=gen.random((12,members))<p
        next_sim=np.zeros_like(sim)
        for site in range(12):
            pool=wet_pools[site][d]
            draws=gen.choice(pool,size=members)
            conditional=np.maximum(1,mu[site]/np.maximum(p[site],.05))
            scaled=np.maximum(1,draws*conditional/pool.mean())
            next_sim[site]=np.where(wet[site],scaled,0)
            if s=='2026-10-20': continue
            seas=season(day.month)
            slope,reference=trend[(site,seas)]
            # The historic nine-year local record is centered near 2021.5.
            factor=float(np.clip(1+(slope/reference)*(day.year-2021.5)/10,.9,1.1)) if reference>0 else 1.0
            vals=next_sim[site]
            rows.append([s,names[site],seas,round(float(np.mean(mu[site])),2),
                         round(float(np.mean(p[site])),4),
                         round(float(np.mean(vals>=20)),4),round(float(np.mean(vals>=50)),4),
                         round(float(np.quantile(vals,.5)),2),round(float(np.quantile(vals,.9)),2),
                         round(factor,4),round(float(np.mean(mu[site])*factor),2)])
        sim=next_sim

assert len(rows)==12*1096 and rows[0][0]=='2026-10-21' and rows[-1][0]=='2029-10-20'
Path('data/lstm_outlook_rows.json').write_text(json.dumps({'rows':rows,'trend':{f'{names[i]}|{s}':v for (i,s),v in trend.items()},
                                                       'as_of':'2026-10-20','last_observation':'2026-10-19',
                                                       'ensemble_members':members}))
torch.save({'state_dict':model.state_dict(),'trained_through':'2026-10-19',
            'model':'12-site embedding; 24-unit LSTM; wet odds and expected rain heads'},
           'data/lstm_open_meteo_final.pt')
print('created',len(rows),'daily rows',flush=True)
