// JavaScript port of allocation/strategies.py so the simulator runs in the browser.
// Keep the two in sync: same weights, minima, reserve and maths.

export const SECTORS = ['bengaluru', 'domestic', 'environment', 'agriculture']
export const WEIGHTS = { bengaluru: 4, domestic: 3, environment: 2, agriculture: 1 }
export const MINIMA = { bengaluru: 0.85, domestic: 0.8, environment: 0.75, agriculture: 0 }
export const HEDGE_RESERVE = 0.1

const LITRES_PER_TMC = 28316846592
export const BENGALURU = {
  low: { population: 13e6, lpcd: 135, loss: 0.15 },
  medium: { population: 14.5e6, lpcd: 150, loss: 0.2 },
  high: { population: 16e6, lpcd: 165, loss: 0.25 },
}

export function monthlyDemand(level = 'medium', days = 30) {
  const b = BENGALURU[level]
  return {
    bengaluru: (b.population * b.lpcd * days) / (1 - b.loss) / LITRES_PER_TMC,
    domestic: 0.3,
    environment: 0.25,
    agriculture: 250.62 * 0.1,
  }
}

const sum = (o) => SECTORS.reduce((a, k) => a + o[k], 0)
const map = (f) => Object.fromEntries(SECTORS.map((k) => [k, f(k)]))

function fillInOrder(supply, wants, order) {
  const out = {}
  for (const k of order) {
    out[k] = Math.min(wants[k], supply)
    supply -= out[k]
  }
  return [out, supply]
}

function cutUntil(supply, demand, shortfall, hi = 1e6) {
  const total = sum(demand)
  let lo = 0
  for (let i = 0; i < 200; i++) {
    const mid = (lo + hi) / 2
    if (total - sum(shortfall(mid)) > supply) lo = mid
    else hi = mid
  }
  const s = shortfall(hi)
  return map((k) => demand[k] - s[k])
}

const essentialPriority = (S, d) => fillInOrder(S, d, SECTORS)[0]

const proportional = (S, d) => {
  const share = Math.min(1, S / sum(d))
  return map((k) => d[k] * share)
}

function minimumGuarantee(S, d) {
  const floors = map((k) => d[k] * MINIMA[k])
  const [first, left] = fillInOrder(S, floors, SECTORS)
  const rest = map((k) => d[k] - first[k])
  const [second] = fillInOrder(left, rest, ['agriculture', 'bengaluru', 'domestic', 'environment'])
  return map((k) => first[k] + second[k])
}

const weightedCuts = (S, d) =>
  S >= sum(d) ? { ...d } : cutUntil(S, d, (mu) => map((k) => Math.min(d[k], (mu * d[k]) / WEIGHTS[k])))

const equalCuts = (S, d) =>
  S >= sum(d) ? { ...d } : cutUntil(S, d, (lam) => map((k) => Math.min(d[k], lam)))

const optimised = (S, d) =>
  S >= sum(d) ? { ...d } : cutUntil(S, d, (mu) => map((k) => Math.min(d[k], (mu * d[k] * d[k]) / WEIGHTS[k])))

function droughtHedging(S, d) {
  if (S >= sum(d)) return { ...d, reserve: 0 }
  const reserve = S * HEDGE_RESERVE
  return { ...minimumGuarantee(S - reserve, d), reserve }
}

export const RULES = {
  essential_priority: essentialPriority,
  proportional,
  minimum_guarantee: minimumGuarantee,
  weighted_cuts: weightedCuts,
  equal_cuts: equalCuts,
  optimised,
  drought_hedging: droughtHedging,
}

export function runAll(supply, demand) {
  return Object.entries(RULES).map(([id, rule]) => {
    const a = rule(supply, demand)
    return {
      id,
      allocation: a,
      satisfaction: map((k) => (100 * a[k]) / demand[k]),
      deficit: SECTORS.reduce((t, k) => t + demand[k] - a[k], 0),
      reserve: a.reserve || 0,
    }
  })
}
