#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

# Bundled fixed snapshots make the default run independent of API availability.
# Pass --refresh to download them again from Open-Meteo first.
if [[ "${1:-}" == "--refresh" ]]; then
  python fetch_era5.py
  python fetch_ifs.py
  python fetch_ifs_2026.py
  python fetch_climate_anchors.py --force
elif [[ "${1:-}" != "" ]]; then
  echo "Usage: ./run_all.sh [--refresh]" >&2
  exit 2
fi

python analyze_rainfall.py
# build_lstm_outlook.py executes lstm_open_meteo.py, trains/validates, then refits.
python build_lstm_outlook.py
python analyze_climate_ensemble.py
python export_final_csv.py
echo 'Done. Final tables are in outputs/.'
