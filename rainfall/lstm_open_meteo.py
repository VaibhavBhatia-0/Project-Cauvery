"""Causal, Open-Meteo-only rainfall LSTM; 2017–22 train, 2023–25 blind test.

Only calendar, location, ERA5 climate normals, and simulated previous rainfall
are available at a multi-year forecast horizon. No future observed rain enters
the blind test. The one-step teacher-forced test is reported separately.
"""
import datetime as dt
import json
import math
from pathlib import Path

import numpy as np
import torch
from torch import nn
from torch.nn import functional as F

torch.set_num_threads(2)
torch.manual_seed(37)
np.random.seed(37)
IFS=json.loads(Path('data/ifs_12sites_2017_2025.json').read_text())
ERA=json.loads(Path('data/era5_12sites_1991_2025.json').read_text())

def doy(s):
    return (dt.date(2000,int(s[5:7]),int(s[8:10]))-dt.date(2000,1,1)).days

def base_normals(site):
    bins=[[] for _ in range(366)]
    for s,v in zip(ERA[site]['daily']['time'],ERA[site]['daily']['rain_sum']):
        if int(s[:4])<=2022 and v is not None: bins[doy(s)].append(v)
    normal=np.zeros((366,2),dtype=np.float32)
    for d in range(366):
        a=np.array([x for step in range(-15,16) for x in bins[(d+step)%366]])
        normal[d]=[np.log1p(a.mean())/4, np.mean(a>=1)]
    return normal

normal=np.stack([base_normals(i) for i in range(12)])
seqs=[]; targets=[]; site_ids=[]
all_dates=IFS[0]['daily']['time']
all_vals=np.stack([np.array([np.nan if x is None else x for x in a['daily']['rain_sum']]) for a in IFS])
assert all_dates[0]=='2017-01-01' and all_dates[-1]=='2025-12-31'
def feature(site,day_index,previous_rain):
    d=doy(all_dates[day_index]);ang=2*math.pi*d/366
    return [np.log1p(max(0,previous_rain))/4, float(previous_rain>=1),
            math.sin(ang),math.cos(ang),math.sin(2*ang),math.cos(2*ang),
            normal[site,d,0],normal[site,d,1]]

train_end=all_dates.index('2023-01-01')
for site in range(12):
    for start in range(2,train_end,90):
        stop=min(start+90,train_end)
        x=np.array([feature(site,t,all_vals[site,t-1]) for t in range(start,stop)],dtype=np.float32)
        y=np.array([all_vals[site,t] for t in range(start,stop)],dtype=np.float32)
        if np.isfinite(x).all() and np.isfinite(y).all():
            seqs.append(torch.from_numpy(x));targets.append(torch.from_numpy(y));site_ids.append(site)
assert len(seqs)>250

class RainLSTM(nn.Module):
    def __init__(self):
        super().__init__()
        self.site=nn.Embedding(12,4)
        self.rnn=nn.LSTM(12,24,batch_first=True)
        self.out=nn.Linear(24,2)
    def forward(self,x,site,h=None):
        emb=self.site(site)[:,None,:].expand(-1,x.shape[1],-1)
        z,h=self.rnn(torch.cat([x,emb],-1),h)
        logits,mean_raw=self.out(z).unbind(-1)
        return logits,F.softplus(mean_raw)+.01,h

model=RainLSTM()
optim=torch.optim.AdamW(model.parameters(),lr=.003,weight_decay=.02)
for epoch in range(12):
    perm=torch.randperm(len(seqs))
    losses=[]
    model.train()
    for idx in perm.split(20):
        # 90-day equal-size chunks except at year boundary; separately batch partial chunks.
        groups={}
        for k in idx.tolist(): groups.setdefault(len(seqs[k]),[]).append(k)
        for group in groups.values():
            x=torch.stack([seqs[k] for k in group]);y=torch.stack([targets[k] for k in group])
            s=torch.tensor([site_ids[k] for k in group])
            logits,mu,_=model(x,s)
            wet=(y>=1).float()
            # Poisson quasi-likelihood learns the conditional mean without inventing a
            # precise count distribution for rainfall; BCE trains the wet-day odds.
            loss=F.binary_cross_entropy_with_logits(logits,wet)+(mu-y*torch.log(mu)).mean()*.15
            optim.zero_grad();loss.backward();nn.utils.clip_grad_norm_(model.parameters(),1.0);optim.step()
            losses.append(float(loss.detach()))
    if epoch in (0,5,11): print('epoch',epoch+1,'loss',round(float(np.mean(losses)),3),flush=True)

model.eval()
start=train_end
stop=len(all_dates)
N=stop-start
obs=all_vals[:,start:stop]
assert np.isfinite(obs).all()

# True one-day-ahead evaluation receives yesterday's observed rain. It cannot
# be used as a three-year score but reveals whether the LSTM learned persistence.
one_p=np.zeros_like(obs);one_mu=np.zeros_like(obs)
with torch.no_grad():
    for site in range(12):
        h=None
        for t in range(start,stop):
            x=torch.tensor([[feature(site,t,all_vals[site,t-1])]],dtype=torch.float32)
            logits,mu,h=model(x,torch.tensor([site]),h)
            one_p[site,t-start]=float(torch.sigmoid(logits)[0,0])
            one_mu[site,t-start]=float(mu[0,0])

# For three-year outlooks, sample prior rainfall from the LSTM itself. Each
# member is one plausible wet/dry sequence. No 2023–25 observed value is input.
members=64
sim_p=np.zeros((12,N),dtype=np.float32)
sim_mu=np.zeros((12,N),dtype=np.float32)
sim_rain=np.repeat(all_vals[:,start-1,None],members,axis=1).astype(np.float32)
ids=torch.arange(12).repeat_interleave(members)
h=None
with torch.no_grad():
    # Warm recurrent state on a known pre-test 45-day history; it sees no test data.
    for t in range(start-45,start):
        known=np.repeat(all_vals[:,t-1,None],members,axis=1).reshape(-1)
        x=np.array([feature(int(ids[k]),t,known[k]) for k in range(len(ids))],dtype=np.float32)
        _,_,h=model(torch.from_numpy(x)[:,None,:],ids,h)
    for j,t in enumerate(range(start,stop)):
        prev=sim_rain.reshape(-1)
        x=np.array([feature(int(ids[k]),t,prev[k]) for k in range(len(ids))],dtype=np.float32)
        logits,mu,h=model(torch.from_numpy(x)[:,None,:],ids,h)
        p=torch.sigmoid(logits[:,0]).numpy().reshape(12,members)
        amount=mu[:,0].numpy().reshape(12,members)
        sim_p[:,j]=p.mean(axis=1)
        sim_mu[:,j]=amount.mean(axis=1)
        wet=np.random.random((12,members))<p
        # Mean among wet days preserves the expected amount from the model.
        conditional=np.maximum(1.0,amount/np.maximum(p,.05))
        sampled=1+np.random.gamma(1.6,np.maximum(.01,(conditional-1)/1.6)).astype(np.float32)
        sim_rain=np.where(wet,sampled,0.0).astype(np.float32)

# Historical baseline is frozen at 2022, exactly as the LSTM training inputs.
clim_p=np.zeros((12,N));clim_mu=np.zeros((12,N))
for site in range(12):
    bins=[[] for _ in range(366)]
    for t in range(train_end):
        if np.isfinite(all_vals[site,t]): bins[doy(all_dates[t])].append(all_vals[site,t])
    for j,t in enumerate(range(start,stop)):
        d=doy(all_dates[t]);values=np.array([x for shift in range(-15,16) for x in bins[(d+shift)%366]])
        clim_p[site,j]=np.mean(values>=1)
        clim_mu[site,j]=values.mean()

def scores(p,mu,a):
    wet=(a>=1).astype(float)
    return {'brier':round(float(np.mean((p-wet)**2)),5),
            'mae_mm_day':round(float(np.mean(np.abs(mu-a))),3),
            'mean_bias_mm_day':round(float(np.mean(mu-a)),3)}

result={'description':'Open-Meteo IFS 2017–2022 train, ERA5 1991–2022 climate normals; 2023–2025 blind recursive test',
        'n_days_per_site':N,'ensemble_members':members,'models':{}}
for label,p,mu in [('baseline',clim_p,clim_mu),('lstm_blind',sim_p,sim_mu),('lstm_one_day',one_p,one_mu)]:
    result['models'][label]={'pooled':scores(p,mu,obs),
                             'annual':{str(year):scores(p[:,[d[:4]==str(year) for d in all_dates[start:stop]]],
                                                         mu[:,[d[:4]==str(year) for d in all_dates[start:stop]]],
                                                         obs[:,[d[:4]==str(year) for d in all_dates[start:stop]]])
                                       for year in (2023,2024,2025)}}
print(json.dumps(result,indent=2),flush=True)
Path('data/lstm_open_meteo_test.json').write_text(json.dumps(result,indent=2))
np.savez_compressed('data/lstm_open_meteo_test_arrays.npz',dates=np.array(all_dates[start:stop]),
                    observed=obs,blind_p=sim_p,blind_mean=sim_mu,
                    one_day_p=one_p,one_day_mean=one_mu,
                    baseline_p=clim_p,baseline_mean=clim_mu)
torch.save({'state_dict':model.state_dict(),'source':'Open-Meteo IFS and ERA5 through 2022',
            'architecture':'Embedding(12,4); LSTM(input=12,hidden=24); wet probability and positive expected rainfall heads'},
           'data/lstm_open_meteo_prototype.pt')
