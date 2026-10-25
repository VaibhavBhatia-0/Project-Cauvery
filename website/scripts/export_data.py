"""Collect the numbers the website charts need into one small JSON file.

Run from the repository root after the rainfall and allocation pipelines:
    python website/scripts/export_data.py
"""
import csv
import json
from collections import defaultdict
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
RAIN = ROOT / 'rainfall' / 'data'
OUT = ROOT / 'website' / 'src' / 'data' / 'projectData.json'

CATCHMENT = {
    'Somwarpet': 'Harangi', 'Madikeri': 'Harangi',
    'Mudigere': 'Hemavathi', 'Sakleshpur': 'Hemavathi', 'Hassan': 'Hemavathi',
    'Bhagamandala': 'KRS', 'Kushalnagar': 'KRS', 'Hunsur': 'KRS',
    'Mananthavady': 'Kabini', 'Kalpetta': 'Kabini', 'H.D. Kote': 'Kabini', 'Gundlupet': 'Kabini',
}

# Test-split metrics written by the reservoir delta-LSTM run (TMC, next-day storage).
RESERVOIR_METRICS = [
    {'name': 'Harangi',   'lstm_mae': 0.0683, 'persist_mae': 0.0607, 'lstm_rmse': 0.1124, 'persist_rmse': 0.1095, 'lstm_r2': 0.9971, 'persist_r2': 0.9972},
    {'name': 'Hemavathi', 'lstm_mae': 0.1298, 'persist_mae': 0.1418, 'lstm_rmse': 0.2191, 'persist_rmse': 0.2813, 'lstm_r2': 0.9993, 'persist_r2': 0.9989},
    {'name': 'KRS',       'lstm_mae': 0.1555, 'persist_mae': 0.2406, 'lstm_rmse': 0.2712, 'persist_rmse': 0.4668, 'lstm_r2': 0.9996, 'persist_r2': 0.9988},
    {'name': 'Kabini',    'lstm_mae': 0.3970, 'persist_mae': 0.1231, 'lstm_rmse': 0.8401, 'persist_rmse': 0.2338, 'lstm_r2': 0.9665, 'persist_r2': 0.9974},
]


def scores(pred, obs):
    err = pred - obs
    return {'mae': round(float(np.abs(err).mean()), 3),
            'rmse': round(float(np.sqrt((err ** 2).mean())), 3),
            'r2': round(float(1 - (err ** 2).sum() / ((obs - obs.mean()) ** 2).sum()), 3)}


def main():
    analysis = json.loads((RAIN / 'rainfall_analysis.json').read_text())
    test = json.loads((RAIN / 'lstm_open_meteo_test.json').read_text())
    climate = json.loads((RAIN / 'climate_ensemble_factors.json').read_text())
    arrays = np.load(RAIN / 'lstm_open_meteo_test_arrays.npz')
    alloc = json.loads((ROOT / 'allocation' / 'outputs' / 'allocation_results.json').read_text())

    sites = []
    for i, r in enumerate(analysis['sites']):
        obs = arrays['observed'][i]
        sites.append({
            'name': r[0], 'district': r[1], 'state': r[2], 'lat': r[3], 'lon': r[4],
            'catchment': CATCHMENT[r[0]], 'annual_mm': r[12], 'trend_mm_decade': r[13],
            'lstm': scores(arrays['blind_mean'][i], obs),
            'baseline': scores(arrays['baseline_mean'][i], obs),
        })

    # Basin-average ERA5 annual rainfall, 1991-2025.
    by_year = defaultdict(list)
    for town, year, total, monsoon, *_ in analysis['annual']:
        by_year[year].append((total, monsoon))
    era5 = [{'year': y, 'total': round(np.mean([t for t, _ in v])), 'monsoon': round(np.mean([m for _, m in v]))}
            for y, v in sorted(by_year.items())]

    # Average full-year scenario across the 12 towns.
    future = defaultdict(lambda: defaultdict(list))
    with (ROOT / 'rainfall' / 'outputs' / 'lstm_climate_annual_2026_2029.csv').open() as fh:
        for row in csv.DictReader(fh):
            if row['days'] in ('365', '366'):
                for k in ('historical_mm', 'lstm_blend_mm', 'climate_low_mm', 'climate_median_mm', 'climate_high_mm'):
                    future[row['year']][k].append(float(row[k]))
    scenarios = [{'year': int(y), **{k: round(np.mean(v)) for k, v in d.items()}} for y, d in sorted(future.items())]

    data = {
        'rainfall': {
            'sites': sites,
            'pooled': {k: v['pooled'] for k, v in test['models'].items()},
            'annual_scores': {k: v['annual'] for k, v in test['models'].items()},
            'era5_annual': era5,
            'future_annual': scenarios,
            'climate_factors': [{'season': s['season'], **{k: s['rain_total'][k] for k in ('median', 'p10', 'p90')}}
                                for s in climate['summary']],
        },
        'reservoirs': {'metrics': RESERVOIR_METRICS, 'forecast_tmc': alloc['reservoir_forecast_tmc'],
                       'design_capacity_tmc': alloc['design_capacity_tmc']},
        'allocation': alloc,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(data, separators=(',', ':')))
    print(f'Wrote {OUT} ({OUT.stat().st_size // 1024} KB)')


if __name__ == '__main__':
    main()
