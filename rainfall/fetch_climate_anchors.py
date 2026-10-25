"""Download seven Open-Meteo climate models at the four sampled locations."""
import json
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

COORDS = [(12.596, 75.849), (12.425, 75.739),
          (13.133, 75.641), (12.941, 75.785)]
MODELS = ['CMCC_CM2_VHR4', 'FGOALS_f3_H', 'HiRAM_SIT_HR',
          'MRI_AGCM3_2_S', 'EC_Earth3P_HR', 'MPI_ESM1_2_XR', 'NICAM16_8S']
# Kept under its original filename for compatibility; it contains FOUR sites.
TARGET = Path('data/climate_7models_12sites_1995_2029.json')


def main(force=False):
    if TARGET.exists() and not force:
        cached = json.loads(TARGET.read_text())
        if len(cached) == 4:
            print('Complete four-site climate cache exists; use --force to redownload.')
            return
    out = []
    for i in range(0, 4, 2):
        chunk = COORDS[i:i + 2]
        params = {'latitude': ','.join(str(x) for x, _ in chunk),
                  'longitude': ','.join(str(y) for _, y in chunk),
                  'start_date': '1995-01-01', 'end_date': '2029-12-31',
                  'daily': 'precipitation_sum', 'models': ','.join(MODELS)}
        url = 'https://climate-api.open-meteo.com/v1/climate?' + urllib.parse.urlencode(params)
        for attempt in range(8):
            try:
                with urllib.request.urlopen(url, timeout=240) as response:
                    received = json.load(response)
                if isinstance(received, dict):
                    received = [received]
                assert len(received) == len(chunk)
                assert all(len(site['daily']['time']) == 12784 and all(
                    len(site['daily'][f'precipitation_sum_{model}']) == 12784
                    for model in MODELS) for site in received)
                out.extend(received)
                print(f'Climate locations {i + 1}–{i + len(chunk)} received', flush=True)
                break
            except Exception as exc:
                if attempt == 7:
                    raise
                delay = min(90, 8 * (attempt + 1))
                print(f'{exc}; retry in {delay}s', flush=True)
                time.sleep(delay)
        time.sleep(8)
    assert len(out) == 4
    TARGET.parent.mkdir(parents=True, exist_ok=True)
    tmp = TARGET.with_suffix('.json.tmp')
    tmp.write_text(json.dumps(out))
    tmp.replace(TARGET)
    print(f'Saved {TARGET}', flush=True)


if __name__ == '__main__':
    main('--force' in sys.argv[1:])
