import { useMemo, useState } from 'react'
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Cell, LabelList } from 'recharts'
import data from '../data/projectData.json'
import { STRATEGIES, SECTOR_LABEL, SECTOR_COLOR, STRATEGY_COLOR } from '../content.js'
import { SECTORS, monthlyDemand, runAll } from '../lib/allocation.js'
import { ChartTip, axis, grid, cursor } from './ui.jsx'

const alloc = data.allocation
const demand = monthlyDemand('medium')
const total = SECTORS.reduce((a, k) => a + demand[k], 0)

export default function Allocate() {
  const [pct, setPct] = useState(75)
  const [pick, setPick] = useState(0)
  const supply = (total * pct) / 100
  const results = useMemo(() => runAll(supply, demand), [supply])
  const s = STRATEGIES[pick]
  const r = results[pick]
  const bars = SECTORS.map((k) => ({ key: k, name: SECTOR_LABEL[k], v: +r.satisfaction[k].toFixed(1) }))

  return (
    <section id="allocation" className="band">
      <div className="container">
        <div className="head-row reveal">
          <p className="tag">The main part</p>
          <h2 className="display">Seven ways to share a shortage</h2>
          <p className="body-lg">
            This October the forecast is <b>{alloc.cases.model_based.supply_tmc.toFixed(1)} TMC</b> against <b>{total.toFixed(1)} TMC</b> of
            demand, so every rule gives everyone 100%. The interesting part is what happens when supply drops.
            Pick a rule, drag the slider.
          </p>
        </div>

        <div className="panel reveal">
          <div className="panel-controls">
            <label className="slider">
              <span>Water available <b>{pct}%</b> of demand · {supply.toFixed(1)} TMC</span>
              <input type="range" min="20" max="100" value={pct} onChange={(e) => setPct(+e.target.value)}
                style={{ '--fill': `${((pct - 20) / 80) * 100}%` }} />
            </label>
            <div className="pills" role="tablist">
              {STRATEGIES.map((st, i) => (
                <button key={st.id} role="tab" aria-selected={i === pick} className={i === pick ? 'on' : ''} onClick={() => setPick(i)}>
                  <i style={{ background: STRATEGY_COLOR[i] }} />{st.name}
                </button>
              ))}
            </div>
          </div>

          <div className="panel-body">
            <div className="explain" key={s.id}>
              <span className="explain-tag" style={{ color: STRATEGY_COLOR[pick] }}>Rule {pick + 1} · {s.tag}</span>
              <h3>{s.name}</h3>
              <p className="explain-idea">{s.idea}</p>
              <p className="explain-how">{s.how}</p>
              <code className="formula">{s.formula}</code>
              <ul className="proscons">
                <li><b className="g">+</b>{s.pro}</li>
                <li><b className="r">−</b>{s.con}</li>
              </ul>
            </div>
            <div className="explain-chart">
              <div className="chart-top">
                <span>% of each sector's demand met</span>
                <span className="kpis">
                  Shortfall <b>{r.deficit.toFixed(2)} TMC</b>
                  {r.reserve > 0 && <> · Reserve <b>{r.reserve.toFixed(2)} TMC</b></>}
                </span>
              </div>
              <ResponsiveContainer width="100%" height={260}>
                <BarChart data={bars} margin={{ top: 22, right: 8, left: -14, bottom: 0 }}>
                  <CartesianGrid {...grid} />
                  <XAxis dataKey="name" {...axis} />
                  <YAxis {...axis} domain={[0, 100]} ticks={[0, 25, 50, 75, 100]} tickFormatter={(v) => `${v}%`} />
                  <Tooltip cursor={cursor} content={<ChartTip unit="%" digits={1} />} />
                  <Bar dataKey="v" name="Demand met" radius={[6, 6, 0, 0]} maxBarSize={64} isAnimationActive={false}>
                    {bars.map((b) => <Cell key={b.key} fill={SECTOR_COLOR[b.key]} />)}
                    <LabelList dataKey="v" position="top" formatter={(v) => `${Math.round(v)}%`} fill="#f2f2f2" fontSize={13} fontWeight={600} />
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>

          <div className="compare">
            <div className="compare-head">
              <span>All seven rules at {pct}% supply</span>
              <span className="muted">Brighter = more of the demand met. Click a row.</span>
            </div>
            <div className="heat" role="table">
              <div className="heat-row heat-h" role="row">
                <span />
                {SECTORS.map((k) => <span key={k} role="columnheader"><i style={{ background: SECTOR_COLOR[k] }} />{SECTOR_LABEL[k]}</span>)}
                <span role="columnheader">Shortfall</span>
              </div>
              {results.map((row, i) => (
                <button key={row.id} className={`heat-row ${i === pick ? 'on' : ''}`} onClick={() => setPick(i)} role="row">
                  <span className="heat-name"><i style={{ background: STRATEGY_COLOR[i] }} />{STRATEGIES[i].name}</span>
                  {SECTORS.map((k) => {
                    const v = row.satisfaction[k]
                    return (
                      <span key={k} className="cell" style={{ background: `color-mix(in srgb, ${SECTOR_COLOR[k]} ${Math.round(8 + v * 0.62)}%, transparent)` }}>
                        {Math.round(v)}%
                      </span>
                    )
                  })}
                  <span className="cell plain">{row.deficit.toFixed(1)}</span>
                </button>
              ))}
            </div>
          </div>
        </div>
        <p className="note-line reveal">
          The first six rules leave the <b>same total shortfall</b>. A rule never creates water, it only decides who carries the cut.
          Hedging is the exception: it keeps a reserve for next month.
        </p>
      </div>
    </section>
  )
}
