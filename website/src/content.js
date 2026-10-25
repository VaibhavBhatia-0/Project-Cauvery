// Plain-English copy for the site. Numbers come from src/data/projectData.json.

export const AUTHOR = 'Vaibhav Bhatia'
export const GITHUB_URL = '' // e.g. 'https://github.com/<you>/cauvery-water-allocation'

export const SECTOR_LABEL = {
  bengaluru: 'Bengaluru',
  domestic: 'Other towns',
  environment: 'River ecology',
  agriculture: 'Agriculture',
}

export const SECTOR_COLOR = {
  bengaluru: '#3987e5',
  domestic: '#d95926',
  environment: '#199e70',
  agriculture: '#c98500',
}

// Dark-surface steps of the validated palette, fixed categorical order for the seven strategies (never cycled).
export const STRATEGY_COLOR = ['#3987e5', '#d95926', '#199e70', '#c98500', '#d55181', '#008300', '#9085e9']

export const STRATEGIES = [
  {
    id: 'essential_priority',
    name: 'Essential Priority',
    tag: 'Strict ladder',
    idea: 'Drinking water first, farms last. Each sector is filled completely before the next one gets anything.',
    how: 'Bengaluru → other towns → river ecology → agriculture, in that order, until the water runs out.',
    formula: 'xᵢ = min(dᵢ, S − Σⱼ₍ⱼ<ᵢ₎ xⱼ)',
    pro: 'Cities and the river are fully protected.',
    con: 'Agriculture absorbs 100% of every shortage.',
  },
  {
    id: 'proportional',
    name: 'Proportional',
    tag: 'Equal percentage',
    idea: 'Everyone gets the same percentage of what they asked for. 75% of the water means 75% for everyone.',
    how: 'Share = supply ÷ total demand, applied to each sector.',
    formula: 'xᵢ = dᵢ · min(1, S / D)',
    pro: 'Simple, transparent and easy to defend.',
    con: 'Drinking water is cut just as hard as irrigation.',
  },
  {
    id: 'minimum_guarantee',
    name: 'Minimum Guarantee',
    tag: 'Floors, then farms',
    idea: 'Guarantee a minimum share to essential uses, give the rest to agriculture, then top up.',
    how: 'Floors of 85% (Bengaluru), 80% (towns), 75% (ecology) are met first; agriculture next; leftovers top up the floors.',
    formula: 'xᵢ ≥ mᵢ·dᵢ, then agriculture, then top-ups',
    pro: 'Balances people and farms; floors are explicit, tunable policy knobs.',
    con: 'The floor values are a judgement call, not data.',
  },
  {
    id: 'weighted_cuts',
    name: 'Weighted Cuts',
    tag: 'Shared pain by importance',
    idea: 'Everyone takes a cut, but less important uses are cut harder. Nobody is fully protected or fully sacrificed.',
    how: 'Weights 4 : 3 : 2 : 1 (Bengaluru : towns : ecology : farms). Satisfaction = 1 − μ / weight, with μ found by bisection.',
    formula: 'satᵢ = 1 − μ / wᵢ',
    pro: 'Smooth trade-off; the shortage is visible to every sector.',
    con: 'Cities feel some shortage even in a mild drought.',
  },
  {
    id: 'equal_cuts',
    name: 'Equal Cuts',
    tag: 'Cautionary rule',
    idea: 'Cut every sector by the same number of TMC. Sounds fair, but demands differ by 100×.',
    how: 'Each sector loses λ TMC (never below zero); λ is set so the total matches supply.',
    formula: 'xᵢ = max(0, dᵢ − λ)',
    pro: 'Easy to explain in one sentence.',
    con: 'Wipes out small users first: at 75% supply, Bengaluru gets 0%. Kept to show why "equal" ≠ "fair".',
  },
  {
    id: 'optimised',
    name: 'Optimised',
    tag: 'Minimise weighted shortage²',
    idea: 'Treat allocation as an optimisation problem: minimise the total weighted squared shortage.',
    how: 'Minimise Σ wᵢ (shortfallᵢ / dᵢ)². The KKT conditions give shortfallᵢ = min(dᵢ, μ·dᵢ² / wᵢ), solved by bisection.',
    formula: 'min Σ wᵢ (sᵢ / dᵢ)²  s.t. Σ xᵢ = S',
    pro: 'Spreads a tiny cut to everyone; the largest user absorbs most, because a 1% cut there frees the most water.',
    con: 'Result depends on the chosen weights and loss shape.',
  },
  {
    id: 'drought_hedging',
    name: 'Drought Hedging',
    tag: 'Keep a reserve',
    idea: 'In a shortage, don\'t release everything. Keep 10% back in the reservoir in case next month is worse.',
    how: 'If supply < demand, hold 10% as carry-over storage and share the remaining 90% using Minimum Guarantee.',
    formula: 'release = 0.9·S  when S < D',
    pro: 'Classic reservoir-operations idea: a small cut now to avoid a severe one later.',
    con: 'Larger deficit this month; the benefit only shows over several months.',
  },
]

export const STACK = [
  { group: 'Machine learning', items: ['PyTorch (rainfall LSTM)', 'TensorFlow / Keras (reservoir LSTMs)', 'scikit-learn (scalers, metrics)'] },
  { group: 'Data & analysis', items: ['Python', 'NumPy', 'pandas', 'SciPy (Theil–Sen trends)'] },
  { group: 'Data sources', items: ['Open-Meteo: ERA5 & ECMWF IFS', 'Open-Meteo Climate API (7 models)', 'NWIC reservoir records', 'Cauvery Tribunal report'] },
  { group: 'This website', items: ['React', 'Vite', 'Recharts', 'Vercel'] },
]
