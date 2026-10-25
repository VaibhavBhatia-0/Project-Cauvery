// The three pipeline stages, explained for someone new to the project.
// `layers` draws the architecture diagram; the last layer is the model's output.
export const ML_STEPS = [
  {
    key: 'rain',
    title: 'Predict the rain',
    kind: 'Deep learning · sequence model',
    tech: 'PyTorch',
    plain: "An LSTM is a neural network with memory: it reads days in order and remembers what came before. One shared model learns how today's rain at each of 12 towns depends on the previous days and the time of year.",
    layers: [
      { name: 'Daily features', sub: '8 numbers per day' },
      { name: 'Town embedding', sub: '4 learned numbers' },
      { name: 'LSTM', sub: '24 units' },
      { name: 'Two output heads', sub: 'P(rain) · expected mm' },
    ],
    specs: [
      ['Inputs', "Yesterday's rain, a wet/dry flag, season (sine/cosine), and the 35-year ERA5 normal for that date."],
      ['Predicts', 'The chance it rains tomorrow, and how many millimetres if it does.'],
      ['Training', 'ECMWF data 2017–2022 in 90-day sequences · 12 epochs · AdamW · loss = binary cross-entropy (rain or not) + Poisson (how much).'],
      ['Testing', 'Blind 3-year test on 2023–2025. The model never sees the real rain and feeds on its own predictions, over 64 simulated runs.'],
    ],
  },
  {
    key: 'dam',
    title: 'Predict the reservoirs',
    kind: 'Deep learning · time-series regression',
    tech: 'TensorFlow / Keras',
    plain: "Four separate LSTMs, one per dam, look at the last 30 days and predict how much the reservoir will rise or fall tomorrow. That change is added to today's level.",
    layers: [
      { name: '30-day window', sub: '6–7 features/day' },
      { name: 'LSTM', sub: '64 units + 20% dropout' },
      { name: 'LSTM', sub: '32 units + 20% dropout' },
      { name: 'Dense', sub: '16 ReLU' },
      { name: 'Output', sub: 'Δ storage (TMC)' },
    ],
    specs: [
      ['Inputs', 'Storage, recent change, inflow, outflow, catchment rainfall (from step 1), day of year, and evaporation where at least 95% complete.'],
      ['Predicts', "Tomorrow's change in storage. Forecast = today + change, clipped between empty and full capacity."],
      ['Training', 'Daily NWIC records 1990–2026 · time-ordered 70/15/15 split · Adam + MSE · early stopping · learning rate halved when it plateaus.'],
      ['Testing', 'The last 15% of dates, never seen in training, compared against persistence ("tomorrow = today").'],
    ],
  },
  {
    key: 'share',
    title: 'Share the water',
    kind: 'Optimisation · decision rules',
    tech: 'Python',
    plain: 'The forecast storage becomes the water available. A demand model estimates what each sector needs, then seven rules share the water and every result is checked for water balance.',
    layers: [
      { name: 'Available water', sub: 'sum of 4 forecasts' },
      { name: 'Demand model', sub: 'city · towns · river · farms' },
      { name: '7 sharing rules', sub: 'ladder · % · floors · KKT …' },
      { name: 'Allocation', sub: '% met per sector' },
    ],
    specs: [
      ['Demand', "Bengaluru = people × litres/day × 30 days ÷ (1 − losses). Plus other towns, a minimum river flow and 10% of the Tribunal's yearly farm figure."],
      ['Rules', 'Fixed priority, equal %, guaranteed floors, weighted cuts, equal cuts, a KKT-optimised rule, and drought hedging.'],
      ['Solving', 'The weighted and optimised rules use bisection to find the cut level that exactly uses up the supply.'],
      ['Checks', 'Nothing negative, no one over-served, and never more released than available. The rules are tested at 100%, 75% and 50% supply.'],
    ],
  },
]

export const ML_PRACTICES = [
  ['No data leakage', 'Scalers are fitted on training data only, and future values are never used as inputs.'],
  ['Time-ordered splits', 'Train on the past, test on the future. No random shuffling across dates.'],
  ['Simple baselines', 'Every model is compared with a naive baseline, not just judged on R².'],
  ['Reproducible', 'Fixed random seeds, saved scalers and frozen data snapshots.'],
]
