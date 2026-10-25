import json
import time
import urllib.parse
import urllib.request
from pathlib import Path

coords=[(12.596,75.849),(12.425,75.739),(13.133,75.641),(12.941,75.785),
        (13.007,76.096),(12.384,75.529),(12.458,75.959),(12.305,76.291),
        (11.802,76.004),(11.609,76.083),(12.089,76.329),(11.807,76.692)]
out=[]
for i in range(0,12,3):
    c=coords[i:i+3]
    q=urllib.parse.urlencode({'latitude':','.join(str(x) for x,y in c),
                              'longitude':','.join(str(y) for x,y in c),
                              'start_date':'2026-01-01','end_date':'2026-10-19',
                              'daily':'rain_sum','timezone':'Asia/Kolkata','models':'ecmwf_ifs'})
    for attempt in range(3):
        try:
            with urllib.request.urlopen('https://archive-api.open-meteo.com/v1/archive?'+q,timeout=90) as f:
                x=json.load(f)
            assert len(x)==3 and all(v['daily']['time'][-1]=='2026-10-19' for v in x)
            out.extend(x)
            print('received',i+1,i+3,flush=True)
            break
        except Exception as e:
            if attempt==2: raise
            time.sleep(3)
Path('data/ifs_12sites_2026_to_oct19.json').write_text(json.dumps(out))
print('missing counts', [sum(v is None for v in x['daily']['rain_sum']) for x in out])
