"""Download the fixed 1991–2025 ERA5 daily rain snapshot for all 12 towns."""
import json
import time
import urllib.parse
import urllib.request
from pathlib import Path

COORDS = [
    (12.596, 75.849), (12.425, 75.739), (13.133, 75.641),
    (12.941, 75.785), (13.007, 76.096), (12.384, 75.529),
    (12.458, 75.959), (12.305, 76.291), (11.802, 76.004),
    (11.609, 76.083), (12.089, 76.329), (11.807, 76.692),
]
TARGET = Path('data/era5_12sites_1991_2025.json')


def main():
    out = []
    for i in range(0, len(COORDS), 3):
        chunk = COORDS[i:i + 3]
        params = {
            'latitude': ','.join(str(lat) for lat, _ in chunk),
            'longitude': ','.join(str(lon) for _, lon in chunk),
            'start_date': '1991-01-01', 'end_date': '2025-12-31',
            'daily': 'rain_sum', 'timezone': 'Asia/Kolkata', 'models': 'era5',
        }
        url = 'https://archive-api.open-meteo.com/v1/archive?' + urllib.parse.urlencode(params)
        for attempt in range(6):
            try:
                with urllib.request.urlopen(url, timeout=180) as response:
                    received = json.load(response)
                assert isinstance(received, list) and len(received) == len(chunk)
                assert all(
                    len(site['daily']['time']) == len(site['daily']['rain_sum']) == 12784
                    and site['daily']['time'][0] == '1991-01-01'
                    and site['daily']['time'][-1] == '2025-12-31'
                    for site in received
                )
                out.extend(received)
                print(f'ERA5 locations {i + 1}–{i + len(chunk)} received', flush=True)
                break
            except Exception as exc:
                if attempt == 5:
                    raise
                delay = min(90, 5 * (2 ** attempt))
                print(f'{exc}; retry in {delay}s', flush=True)
                time.sleep(delay)
    assert len(out) == 12
    TARGET.parent.mkdir(parents=True, exist_ok=True)
    tmp = TARGET.with_suffix('.json.tmp')
    tmp.write_text(json.dumps(out))
    tmp.replace(TARGET)
    print(f'Saved {TARGET}', flush=True)


if __name__ == '__main__':
    main()
