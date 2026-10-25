"""Export the final daily and annual scenarios without a spreadsheet dependency."""
import csv
import datetime as dt
import json
import math
from collections import defaultdict
from pathlib import Path

DATA = Path('data')
OUT = Path('outputs')
FIELDS = [
    'date', 'town', 'district', 'state', 'season', 'lead_day', 'lstm_weight',
    'historical_mm', 'raw_lstm_mm', 'lstm_blend_mm', 'climate_low_mm',
    'climate_median_mm', 'climate_high_mm', 'historical_p_ge_1',
    'raw_lstm_p_ge_1', 'blend_p_ge_1', 'climate_p_ge_1_low',
    'climate_p_ge_1_median', 'climate_p_ge_1_high', 'blend_p_ge_20',
    'climate_p_ge_20_low', 'climate_p_ge_20_median',
    'climate_p_ge_20_high', 'blend_p_ge_50', 'climate_p_ge_50_median',
    'raw_lstm_median_mm', 'raw_lstm_p90_mm',
]


def main():
    historical = json.loads((DATA / 'rainfall_analysis.json').read_text())
    lstm = json.loads((DATA / 'lstm_outlook_rows.json').read_text())
    climate = json.loads((DATA / 'climate_ensemble_factors.json').read_text())
    base = {(r[0], r[2]): r for r in historical['outlook']}
    meta = {r[0]: r for r in historical['sites']}
    factors = {r['season']: r for r in climate['summary']}
    daily = []
    annual = defaultdict(lambda: defaultdict(float))
    annual_days = defaultdict(int)
    origin = dt.date(2026, 10, 20)
    for row in lstm['rows']:
        date, town, season, raw, p_raw, p20_raw, p50_raw, raw_median, raw_p90 = row[:9]
        b = base[(date, town)]
        lead = (dt.date.fromisoformat(date) - origin).days
        weight = math.exp(-lead / 60)
        blend = weight * raw + (1 - weight) * b[8]
        wet = weight * p_raw + (1 - weight) * b[9]
        p20 = weight * p20_raw + (1 - weight) * b[11]
        p50 = weight * p50_raw + (1 - weight) * b[12]
        rain_factor = factors[season]['rain_total']
        wet_factor = factors[season]['wet_days']
        heavy_factor = factors[season]['heavy_days']
        result = [
            date, town, meta[town][1], meta[town][2], season, lead, weight,
            b[8], raw, blend, blend * rain_factor['p10'],
            blend * rain_factor['median'], blend * rain_factor['p90'],
            b[9], p_raw, wet, min(1, wet * wet_factor['p10']),
            min(1, wet * wet_factor['median']), min(1, wet * wet_factor['p90']),
            p20, min(1, p20 * heavy_factor['p10']),
            min(1, p20 * heavy_factor['median']),
            min(1, p20 * heavy_factor['p90']), p50,
            min(1, p50 * heavy_factor['median']), raw_median, raw_p90,
        ]
        daily.append(result)
        key = (town, int(date[:4]))
        annual_days[key] += 1
        for field in FIELDS[7:13]:
            annual[key][field] += result[FIELDS.index(field)]
    assert len(daily) == 12 * 1096
    assert daily[0][0] == '2026-10-21' and daily[-1][0] == '2029-10-20'
    OUT.mkdir(parents=True, exist_ok=True)
    with (OUT / 'lstm_climate_daily_2026_2029.csv').open('w', newline='') as fh:
        writer = csv.writer(fh)
        writer.writerow(FIELDS)
        writer.writerows(daily)
    annual_fields = ['town', 'year', 'days'] + FIELDS[7:13]
    with (OUT / 'lstm_climate_annual_2026_2029.csv').open('w', newline='') as fh:
        writer = csv.writer(fh)
        writer.writerow(annual_fields)
        for town in meta:
            for year in (2026, 2027, 2028, 2029):
                key = (town, year)
                writer.writerow([town, year, annual_days[key]] +
                                [annual[key][field] for field in FIELDS[7:13]])
    print(f'Wrote {len(daily)} daily rows and {len(annual_days)} annual rows to {OUT}')


if __name__ == '__main__':
    main()
