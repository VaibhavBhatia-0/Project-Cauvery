import json, math
from collections import defaultdict
from pathlib import Path
import numpy as np

data=json.loads(Path('data/climate_7models_12sites_1995_2029.json').read_text())
models=['CMCC_CM2_VHR4','FGOALS_f3_H','HiRAM_SIT_HR','MRI_AGCM3_2_S',
        'EC_Earth3P_HR','MPI_ESM1_2_XR','NICAM16_8S']
anchors=['Somwarpet','Madikeri','Mudigere','Sakleshpur']
def season(month):
    return 'Winter' if month<=2 else 'Pre-monsoon' if month<=5 else ('Southwest monsoon' if month<=9 else 'Post-monsoon')
metrics=('rain_total','wet_days','heavy_days')
member_ratios=defaultdict(list)
member_rows=[]
for anchor,site in zip(anchors,data):
    dates=site['daily']['time']
    for model in models:
        vals=site['daily'][f'precipitation_sum_{model}']
        agg=defaultdict(lambda:[0.0,0,0])
        for d,v in zip(dates,vals):
            if v is None: continue
            key=(int(d[:4]),season(int(d[5:7])))
            agg[key][0]+=v;agg[key][1]+=int(v>=1);agg[key][2]+=int(v>=20)
        for seas in ('Winter','Pre-monsoon','Southwest monsoon','Post-monsoon'):
            early=np.array([agg[(y,seas)] for y in range(1995,2015)],dtype=float)
            late=np.array([agg[(y,seas)] for y in range(2015,2030)],dtype=float)
            ratios=[]
            for k,metric in enumerate(metrics):
                a=early[:,k].mean();b=late[:,k].mean();ratio=b/a if a>0 else 1.0
                member_ratios[(seas,metric)].append(ratio);ratios.append(ratio)
            member_rows.append([anchor,model,seas,*ratios])
summary=[]
for seas in ('Winter','Pre-monsoon','Southwest monsoon','Post-monsoon'):
    row={'season':seas}
    for metric in metrics:
        x=np.array(member_ratios[(seas,metric)])
        row[metric]={'median':round(float(np.quantile(x,.5)),4),
                     'p10':round(float(np.quantile(x,.1)),4),
                     'p90':round(float(np.quantile(x,.9)),4),
                     'members':len(x),
                     'increase_share':round(float(np.mean(x>1)),4)}
    summary.append(row)
payload={'baseline_period':'1995-2014','comparison_period':'2015-2029','models':models,
         'anchor_locations':anchors,'summary':summary,'members':member_rows,
         'method':'Ratio of each model-location member recent/future mean to its own historical mean; ensemble median and P10-P90 across 28 members.'}
Path('data/climate_ensemble_factors.json').write_text(json.dumps(payload,indent=2))
for r in summary:
    print(r['season'])
    for m in metrics: print(' ',m,r[m])
