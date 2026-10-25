import json
import time
import urllib.parse
import urllib.request
from pathlib import Path

coords = [
    (12.596,75.849), (12.425,75.739), (13.133,75.641),
    (12.941,75.785), (13.007,76.096), (12.384,75.529),
    (12.458,75.959), (12.305,76.291), (11.802,76.004),
    (11.609,76.083), (12.089,76.329), (11.807,76.692),
]
out=[]
for i in range(0, 12, 3):
    chunk=coords[i:i+3]
    params={"latitude":','.join(str(x) for x,_ in chunk),
            "longitude":','.join(str(y) for _,y in chunk),
            "start_date":"2017-01-01", "end_date":"2025-12-31",
            "daily":"rain_sum", "timezone":"Asia/Kolkata", "models":"ecmwf_ifs"}
    url='https://archive-api.open-meteo.com/v1/archive?'+urllib.parse.urlencode(params)
    for attempt in range(4):
        try:
            with urllib.request.urlopen(url,timeout=90) as f:
                data=json.load(f)
            assert len(data)==3
            assert all(len(x['daily']['time'])==3287 and len(x['daily']['rain_sum'])==3287 for x in data)
            out.extend(data)
            print(f"received sites {i+1}-{i+3}",flush=True)
            break
        except Exception as e:
            if attempt==3: raise
            print(f"retrying {i+1}-{i+3}: {str(e)[:100]}",flush=True)
            time.sleep(2*(attempt+1))
Path('data/ifs_12sites_2017_2025.json').write_text(json.dumps(out))
print(f"saved {len(out)} sites",flush=True)
