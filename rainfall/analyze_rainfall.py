import csv
import datetime as dt
import json
import math
from collections import defaultdict
from pathlib import Path
from statistics import mean, median

from scipy.stats import theilslopes, kendalltau

SITES = [
    ("Somwarpet", "Kodagu", "Karnataka", 12.596,75.849),
    ("Madikeri", "Kodagu", "Karnataka", 12.425,75.739),
    ("Mudigere", "Chikkamagaluru", "Karnataka", 13.133,75.641),
    ("Sakleshpur", "Hassan", "Karnataka", 12.941,75.785),
    ("Hassan", "Hassan", "Karnataka", 13.007,76.096),
    ("Bhagamandala", "Kodagu", "Karnataka", 12.384,75.529),
    ("Kushalnagar", "Kodagu", "Karnataka", 12.458,75.959),
    ("Hunsur", "Mysuru", "Karnataka", 12.305,76.291),
    ("Mananthavady", "Wayanad", "Kerala", 11.802,76.004),
    ("Kalpetta", "Wayanad", "Kerala", 11.609,76.083),
    ("H.D. Kote", "Mysuru", "Karnataka", 12.089,76.329),
    ("Gundlupet", "Chamarajanagar", "Karnataka", 11.807,76.692),
]
ifs = json.loads(Path('data/ifs_12sites_2017_2025.json').read_text())
era = json.loads(Path('data/era5_12sites_1991_2025.json').read_text())
assert len(ifs) == len(era) == len(SITES) == 12

def doy(s):
    return (dt.date(2000, int(s[5:7]), int(s[8:10])) - dt.date(2000,1,1)).days

def quant(xs, q):
    if not xs: return None
    a=sorted(xs); p=(len(a)-1)*q; lo=math.floor(p); hi=math.ceil(p)
    return a[lo]*(hi-p)+a[hi]*(p-lo) if lo != hi else a[lo]

def season(d):
    m=d.month
    return 'Southwest monsoon' if 6<=m<=9 else ('Pre-monsoon' if 3<=m<=5 else ('Post-monsoon' if m>=10 else 'Winter'))

def metric(values):
    n=len(values); wet=[x for x in values if x>=1]
    return [round(mean(values),2), round(len(wet)/n,4),
            round(sum(x>=10 for x in values)/n,4),
            round(sum(x>=20 for x in values)/n,4),
            round(sum(x>=50 for x in values)/n,4),
            round(quant(values,.5),1),round(quant(values,.9),1),
            round(quant(wet,.9),1) if wet else None,n]

outlook=[]; monthly=defaultdict(lambda: [0.0,0.0,0.0,0])
site_rows=[]; annual=[]; backtests=[]
history_path='data/rainfall_history_open_meteo.csv'
with open(history_path,'w',newline='') as fh:
    w=csv.writer(fh)
    w.writerow(['model','town','district','state','requested_lat','requested_lon','model_grid_lat','model_grid_lon','local_date','rain_mm'])
    for i,site in enumerate(SITES):
        name,district,state,lat,lon=site
        for model,pack in [('ERA5',era[i]),('ECMWF IFS',ifs[i])]:
            assert len(pack['daily']['time'])==len(pack['daily']['rain_sum'])
            for date,v in zip(pack['daily']['time'],pack['daily']['rain_sum']):
                w.writerow([model,name,district,state,lat,lon,pack['latitude'],pack['longitude'],date,'' if v is None else v])

        series=[(date,v) for date,v in zip(ifs[i]['daily']['time'],ifs[i]['daily']['rain_sum']) if v is not None]
        bins=[[] for _ in range(366)]
        for date,v in series: bins[doy(date)].append(v)
        windows=[]
        for d in range(366):
            values=[x for offset in range(-15,16) for x in bins[(d+offset)%366]]
            windows.append(metric(values))

        start=dt.date(2026,10,21)
        for day in range(1096):
            d=start+dt.timedelta(days=day)
            vals=windows[doy(d.isoformat())]
            outlook.append([d.isoformat(),d.year,name,district,state,lat,lon,season(d),*vals])
            key=(name,d.strftime('%Y-%m'))
            m=monthly[key]
            m[0]+=vals[0]; m[1]+=vals[1]; m[2]+=vals[3]; m[3]+=1

        by_year=defaultdict(list)
        for date,v in zip(era[i]['daily']['time'],era[i]['daily']['rain_sum']):
            assert v is not None
            by_year[int(date[:4])].append((date,v))
        totals=[]
        for year in range(1991,2026):
            rows=by_year[year]
            assert len(rows)==(366 if year%4==0 else 365)
            year_total=sum(v for _,v in rows)
            monsoon=sum(v for date,v in rows if 6<=int(date[5:7])<=9)
            totals.append(year_total)
            annual.append([name,year,round(year_total,1),round(monsoon,1),round(monsoon/year_total,4),
                           sum(v>=1 for _,v in rows),sum(v>=20 for _,v in rows),sum(v>=50 for _,v in rows)])
        years=list(range(1991,2026))
        slope,intercept,low,high=theilslopes(totals,years,alpha=.95)
        _,p=kendalltau(years,totals)
        ifs_years=defaultdict(list)
        for date,v in series: ifs_years[int(date[:4])].append(v)
        assert [len(ifs_years[y]) for y in range(2018,2026)]==[365,365,366,365,365,365,366,365]
        local_totals=[sum(ifs_years[y]) for y in range(2018,2026)]

        # Strict leave-one-calendar-year-out hindcast: other years supply all +/-15-day windows.
        err=0; base_err=0; mae=0; n=0
        by_doy_year=defaultdict(list)
        for date,v in series: by_doy_year[(int(date[:4]),doy(date))].append(v)
        all_year_wet={y:sum(v>=1 for date,v in series if int(date[:4])!=y)/sum(int(date[:4])!=y for date,v in series)
                      for y in range(2017,2026)}
        for date,v in series:
            yr=int(date[:4]); dd=doy(date)
            training=[x for offset in range(-15,16) for yy in range(2017,2026) if yy!=yr
                      for x in by_doy_year.get((yy,(dd+offset)%366),[])]
            pr=sum(x>=1 for x in training)/len(training)
            obs=int(v>=1)
            err+=(pr-obs)**2
            base_err+=(all_year_wet[yr]-obs)**2
            mae+=abs(mean(training)-v); n+=1
        brier=err/n; base=base_err/n
        backtests.append([name,n,round(brier,4),round(base,4),round(1-brier/base,3),round(mae/n,2)])
        site_rows.append([name,district,state,lat,lon,ifs[i]['latitude'],ifs[i]['longitude'],
                          era[i]['latitude'],era[i]['longitude'],round(mean(local_totals)),
                          round(quant(local_totals,.1)),round(quant(local_totals,.9)),
                          round(mean(totals)),round(slope*10,1),round(low*10,1),round(high*10,1),
                          round(p,3),round(mean(totals[:10])),round(mean(totals[-10:])),
                          round(mean(local_totals)/mean(totals[27:35]),3)])

monthly_rows=[]
for (name,month),m in sorted(monthly.items(),key=lambda x:(x[0][0],x[0][1])):
    monthly_rows.append([name,month,m[3],round(m[0],1),round(m[1],1),round(m[2],1)])

payload={'sites':site_rows,'outlook':outlook,'monthly':monthly_rows,'annual':annual,'backtests':backtests,
         'source_rows':len(SITES)*(12784+3287),
         'model_note':'IFS historical weather 2017-2025; ERA5 reanalysis 1991-2025; Asia/Kolkata rain_sum.'}
Path('data/rainfall_analysis.json').write_text(json.dumps(payload,separators=(',',':')))
print('daily',len(outlook),'monthly',len(monthly_rows),'raw source',payload['source_rows'])
for r in site_rows: print(f'{r[0]:15s} IFS {r[9]:4} (P10-P90 {r[10]}-{r[11]}) ERA5 {r[12]:4} trend {r[13]:+6.1f}/decade [{r[14]:+.1f},{r[15]:+.1f}], p={r[16]:.3f}')
