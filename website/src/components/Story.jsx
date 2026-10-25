import { useState } from 'react'
import data from '../data/projectData.json'
import { STACK, AUTHOR, GITHUB_URL } from '../content.js'
import { ML_STEPS, ML_PRACTICES } from '../mlContent.js'

const alloc = data.allocation
const supply = alloc.cases.model_based.supply_tmc
const demand = alloc.total_demand_tmc
const agriShare = (100 * alloc.demand_tmc.agriculture) / demand
const fullPct = (100 * supply) / data.reservoirs.design_capacity_tmc

export function Numbers() {
  const tiles = [
    { cls: 't-lime', n: supply.toFixed(1), unit: 'TMC', text: `water forecast in 4 reservoirs, ${fullPct.toFixed(0)}% of capacity` },
    { cls: 't-dark', n: demand.toFixed(1), unit: 'TMC', text: 'needed by everyone over a 30-day October window' },
    { cls: 't-dark t2', n: '7', unit: 'rules', text: 'for sharing it, stress-tested at 75% and 50% supply' },
    { cls: 't-white', n: agriShare.toFixed(0), unit: '%', text: 'of the demand is agriculture, so the rule decides how hard farms get hit' },
  ]
  return (
    <section id="numbers" className="band">
      <div className="container numbers">
        <div className="numbers-copy reveal">
          <p className="tag">The project</p>
          <h2 className="display">Rain fills the dams.<br /><span className="hl">Then who gets the water?</span></h2>
          <p className="body-lg">
            Monsoon rain over the Western Ghats fills four Karnataka reservoirs. Bengaluru, other towns, the river
            and farms all draw on them. I predict how much water there will be, estimate how much is needed,
            and compare seven ways of sharing it when there isn't enough.
          </p>
        </div>
        <div className="tiles-wall reveal">
          {tiles.map((t) => (
            <div key={t.cls} className={`ntile ${t.cls}`}>
              <div className="ntile-n">{t.n}<span>{t.unit}</span></div>
              <p>{t.text}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}

const ICONS = {
  rain: (
    <svg viewBox="0 0 64 64" aria-hidden="true"><path d="M20 38a12 12 0 1 1 3-23.6A15 15 0 0 1 51 22a9 9 0 0 1-2 16z" fill="currentColor" opacity=".9" /><path d="M24 46l-3 8M34 46l-3 8M44 46l-3 8" stroke="#c6f432" strokeWidth="4" strokeLinecap="round" /></svg>
  ),
  dam: (
    <svg viewBox="0 0 64 64" aria-hidden="true"><path d="M8 18h14l6 36H8z" fill="currentColor" opacity=".9" /><path d="M30 30c4 0 4 3 8 3s4-3 8-3 4 3 8 3M30 40c4 0 4 3 8 3s4-3 8-3 4 3 8 3M30 50c4 0 4 3 8 3s4-3 8-3 4 3 8 3" stroke="#c6f432" strokeWidth="3.5" fill="none" strokeLinecap="round" /></svg>
  ),
  share: (
    <svg viewBox="0 0 64 64" aria-hidden="true"><path d="M32 6c-8 12-14 19-14 27a14 14 0 0 0 28 0c0-8-6-15-14-27z" fill="currentColor" opacity=".9" /><path d="M32 47v11M32 52l-14 6M32 52l14 6" stroke="#c6f432" strokeWidth="3.5" strokeLinecap="round" /></svg>
  ),
}

// Headline result for each stage, computed from the exported metrics.
function stepResult(key) {
  if (key === 'rain') {
    const p = data.rainfall.pooled
    const wins = data.rainfall.sites.filter((t) => t.lstm.mae < t.baseline.mae).length
    return [`${p.lstm_blind.mae_mm_day.toFixed(2)} mm/day`, `average error vs ${p.baseline.mae_mm_day.toFixed(2)} for the baseline · better at ${wins} of 12 towns`]
  }
  if (key === 'dam') {
    const beats = data.reservoirs.metrics.filter((r) => r.lstm_mae < r.persist_mae).map((r) => r.name)
    return [`${beats.length} of 4`, `dams beat persistence (${beats.join(', ')}); Kabini is clearly worse`]
  }
  const r = alloc.cases.moderate_75.strategies
  return [`${r.essential_priority.deficit.toFixed(2)} TMC`, 'shortfall at 75% supply: identical for six rules, only who carries it changes']
}

export function HowItWorks() {
  const [pick, setPick] = useState(0)
  const s = ML_STEPS[pick]
  const [resultBig, resultText] = stepResult(s.key)
  return (
    <section id="how" className="band band-alt">
      <div className="container">
        <div className="head-row reveal">
          <p className="tag">How it works</p>
          <h2 className="display">Two neural networks,<br /><span className="hl">one decision layer</span></h2>
          <p className="body-lg">
            Rainfall feeds the reservoir model, and the reservoir forecast feeds the allocation. Pick a stage to see
            the model, what goes in, what comes out, and how it was tested.
          </p>
        </div>

        <div className="steps reveal" role="tablist">
          {ML_STEPS.map((st, i) => (
            <button key={st.key} role="tab" aria-selected={i === pick} className={`step ${i === pick ? 'on' : ''}`} onClick={() => setPick(i)}>
              <div className="step-art">{ICONS[st.key]}<span className="step-i">0{i + 1}</span></div>
              <h3>{st.title}</h3>
              <span className="step-kind">{st.kind}</span>
              <span className="step-tech">{st.tech}</span>
            </button>
          ))}
        </div>

        <div className="ml reveal">
          <div className="ml-detail" key={s.key}>
            <p className="ml-plain">{s.plain}</p>
            <div className="arch" aria-label="Model architecture">
              {s.layers.map((l, i) => (
                <div key={i} className={`layer ${i === s.layers.length - 1 ? 'out' : ''}`}>
                  <b>{l.name}</b>
                  <span>{l.sub}</span>
                </div>
              ))}
            </div>
            <div className="ml-grid">
              <dl className="specs">
                {s.specs.map(([k, v]) => (
                  <div key={k}><dt>{k}</dt><dd>{v}</dd></div>
                ))}
              </dl>
              <div className="ml-result">
                <span>Result</span>
                <b>{resultBig}</b>
                <p>{resultText}</p>
              </div>
            </div>
          </div>
        </div>

        <div className="practices reveal">
          {ML_PRACTICES.map(([k, v]) => (
            <div key={k}><b>{k}</b><p>{v}</p></div>
          ))}
        </div>
      </div>
    </section>
  )
}

export function DidYouKnow() {
  const equal = alloc.cases.moderate_75.strategies.equal_cuts.satisfaction_pct
  return (
    <section className="band band-lime">
      <div className="container dyk reveal">
        <p className="dyk-q">Did you know?</p>
        <p className="dyk-a">
          With only 75% of the water, the rule that <em>sounds</em> fairest, cutting everyone by the same amount,
          leaves Bengaluru with <span className="hl-y">{equal.bengaluru.toFixed(0)}%</span> of its drinking water.
        </p>
        <p className="dyk-s">Equal isn't fair when one user asks for 100× more than another. That's why I compare seven rules.</p>
      </div>
    </section>
  )
}

export function Footer() {
  return (
    <footer className="footer">
      <div className="container">
        <div className="built reveal">
          <p className="tag">Built with</p>
          <div className="chips">
            {STACK.flatMap((g) => g.items).map((i) => <span key={i} className="chip">{i}</span>)}
          </div>
          <p className="caveat">
            Caveats: grid rainfall misses local extremes, gross storage isn't the same as releasable water, demand
            figures are assumptions, and the 75% / 50% cases are synthetic tests. A modelling project, not policy advice.
          </p>
        </div>
        <div className="footer-in">
          <span><strong>Cauvery Water Allocation</strong> · a personal ML project by {AUTHOR}</span>
          <span className="footer-links">
            {GITHUB_URL && <a href={GITHUB_URL} target="_blank" rel="noreferrer">Source code</a>}
            <a href="#top">Back to top ↑</a>
          </span>
        </div>
      </div>
    </footer>
  )
}
