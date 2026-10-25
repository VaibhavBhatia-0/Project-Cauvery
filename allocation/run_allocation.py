"""Run all seven strategies on the model-based case and two stress tests."""
import json
from pathlib import Path

from demand import monthly_demand
from strategies import STRATEGIES, check_balance

# Last common date of the four reservoir delta-LSTM forecasts (9 Oct 2026),
# clipped to [0, design gross capacity]. Gross storage is only a proxy for
# releasable water: dead storage is not subtracted.
RESERVOIR_FORECAST_TMC = {
    'Harangi': 5.7406, 'Hemavathi': 15.2238, 'KRS': 24.5452, 'Kabini': 10.5865,
}
DESIGN_CAPACITY_TMC = 114.571

OUT = Path(__file__).parent / 'outputs'


def run(supply, demand):
    rows = {}
    for name, rule in STRATEGIES.items():
        alloc = rule(supply, demand)
        check_balance(supply, demand, alloc)
        rows[name] = {
            'allocation': {k: round(alloc[k], 4) for k in demand},
            'satisfaction_pct': {k: round(100 * alloc[k] / demand[k], 2) for k in demand},
            'deficit': round(sum(demand[k] - alloc[k] for k in demand), 4),
            'reserve': round(alloc.get('reserve', 0.0), 4),
        }
    return rows


def main():
    demand = monthly_demand('medium')
    total = sum(demand.values())
    available = sum(RESERVOIR_FORECAST_TMC.values())
    cases = {
        'model_based': available,
        'moderate_75': 0.75 * total,
        'severe_50': 0.50 * total,
    }
    result = {
        'demand_tmc': {k: round(v, 4) for k, v in demand.items()},
        'total_demand_tmc': round(total, 4),
        'reservoir_forecast_tmc': RESERVOIR_FORECAST_TMC,
        'design_capacity_tmc': DESIGN_CAPACITY_TMC,
        'cases': {c: {'supply_tmc': round(s, 4), 'strategies': run(s, demand)} for c, s in cases.items()},
        'sweep': [{'supply_pct': p, **{n: r['satisfaction_pct'] for n, r in run(total * p / 100, demand).items()}}
                  for p in range(20, 105, 5)],
    }
    OUT.mkdir(exist_ok=True)
    (OUT / 'allocation_results.json').write_text(json.dumps(result, indent=2))

    print(f'Demand {total:.4f} TMC, model-based availability {available:.4f} TMC')
    for case, info in result['cases'].items():
        print(f"\n{case}: supply {info['supply_tmc']} TMC")
        for name, r in info['strategies'].items():
            s = r['satisfaction_pct']
            print(f"  {name:22s} Beng {s['bengaluru']:6.2f}%  Dom {s['domestic']:6.2f}%  "
                  f"Env {s['environment']:6.2f}%  Agri {s['agriculture']:6.2f}%  "
                  f"deficit {r['deficit']:.3f}  reserve {r['reserve']:.3f}")


if __name__ == '__main__':
    main()
