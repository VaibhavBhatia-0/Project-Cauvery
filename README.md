# Cauvery Basin Water Allocation

**Who gets the water when the rain falls short?**

This is a personal machine-learning project on the Karnataka part of the Cauvery basin. It does three things:

1. **Allocation (the main part).** I compare seven strategies for sharing a fixed volume of water between
   Bengaluru, other towns, a minimum river flow and agriculture. Each one is tested on the forecast case
   and on synthetic 75% and 50% shortages.
2. **Reservoir forecasting.** Four LSTMs predict the next-day *change* in storage at Harangi, Hemavathi, KRS and
   Kabini. Each one is compared with persistence ("tomorrow = today").
3. **Rainfall forecasting.** One shared LSTM forecasts daily rain for 12 Western Ghats towns and is blind-tested
   on 2023–2025.

An interactive website walks through the pipeline, the strategies, a live allocation simulator and the results.

## Repository layout

```
rainfall/      Rainfall LSTM, climate-model factors, fixed Open-Meteo snapshots, outputs
allocation/    Demand model, the seven allocation strategies, stress tests
website/       React + Vite + Recharts site (deployed on Vercel)
report/        Full project write-up (.docx)
```

## The seven allocation strategies

| # | Strategy | Rule | At 75% supply (Bengaluru / Agriculture) |
|---|---|---|---|
| 1 | Essential priority | Fill sectors fully in priority order | 100% / 71.6% |
| 2 | Proportional | Same % of demand for everyone | 75% / 75% |
| 3 | Minimum guarantee | Floors of 85/80/75%, then agriculture, then top-ups | 85% / 73.8% |
| 4 | Weighted cuts | satisfaction = 1 − μ / weight (weights 4:3:2:1) | 93.2% / 72.6% |
| 5 | Equal cuts | Same TMC cut for everyone (cautionary) | 0% / 85.3% |
| 6 | Optimised | Minimise Σ w·(shortfall/demand)², solved via KKT + bisection | 99.2% / 71.7% |
| 7 | Drought hedging | Keep 10% in reserve, share the rest by rule 3 | 85% / 65.3% |

Demand for a 30-day October window is 28.49 TMC (Bengaluru 2.88, other towns 0.30, environment 0.25,
agriculture 25.06). The reservoir forecast gives 56.10 TMC, so the forecast case has no shortage. That is why
the strategies are stress-tested.

## Key results

- **Rainfall:** blind 3-year MAE 4.350 mm/day vs 4.659 for the historical baseline. The LSTM is better at
  7 of 12 towns, but it misses the largest downpours.
- **Reservoirs:** Hemavathi and KRS beat persistence. Harangi is slightly worse and Kabini is ~3× worse, even
  though every model has R² > 0.96. A high R² does not make a forecast useful.
- **Allocation:** the first six rules leave the same total shortfall. They only decide *who* carries it.
  Hedging accepts a larger deficit now in exchange for a reserve.

## Running it

Python 3.11+.

```bash
python -m pip install -r requirements.txt
python -m pip install torch==2.4.1+cpu --index-url https://download.pytorch.org/whl/cpu
```

**Allocation** (no ML dependencies):

```bash
cd allocation
python run_allocation.py        # writes outputs/allocation_results.json
```

**Rainfall** (from `rainfall/`; uses the bundled snapshots, `--refresh` re-downloads them):

```bash
cd rainfall
./run_all.sh
```

On Windows, run `python analyze_rainfall.py`, `python build_lstm_outlook.py`,
`python analyze_climate_ensemble.py` and `python export_final_csv.py` in that order.

**Website:**

```bash
python website/scripts/export_data.py   # refresh chart data from the pipelines
cd website
npm install
npm run dev
```

### Deploying to Vercel

Import the repository in Vercel and set **Root Directory** to `website`. Vercel detects Vite automatically
(build `npm run build`, output `dist`).

## Data sources

- Open-Meteo Historical Weather API: ERA5 reanalysis (1991–2025) and ECMWF IFS (2017–2026)
- Open-Meteo Climate API: seven HighResMIP models (1995–2029)
- National Water Informatics Centre: daily reservoir records (1990–2026)
- Cauvery Water Disputes Tribunal (2007), Vol. V: Karnataka agricultural water requirement

## Limitations

Grid-cell rainfall misses local extremes. Gross storage is not the same as releasable water. Kabini's model
is worse than persistence. The urban, domestic and environmental demands are assumptions. The 75% and 50%
cases are synthetic tests. None of this is legal or operational advice on Cauvery water sharing.
