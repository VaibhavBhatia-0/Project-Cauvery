import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip } from 'recharts'
import data from '../data/projectData.json'
import { ChartTip, Legend, axis, grid, cursor } from './ui.jsx'

const MODEL = '#c6f432'
const BASE = '#4b4b4b'

export default function Results() {
  const res = data.reservoirs.metrics
  const beats = res.filter((m) => m.lstm_mae < m.persist_mae).length
  const rain = data.rainfall
  const towns = rain.sites.map((s) => ({ name: s.name, lstm: s.lstm.mae, base: s.baseline.mae }))
  const wins = towns.filter((t) => t.lstm < t.base).length
  const p = rain.pooled
  const gain = (100 * (p.baseline.mae_mm_day - p.lstm_blind.mae_mm_day)) / p.baseline.mae_mm_day
  const kabini = res.find((m) => m.name === 'Kabini')

  return (
    <section id="results" className="band band-alt">
      <div className="container">
        <div className="head-row reveal">
          <p className="tag">The predictions</p>
          <h2 className="display">Do the forecasts actually work?</h2>
          <p className="body-lg">Every model is tested on years it never saw and compared with a simple baseline. Some win, some don't.</p>
        </div>

        <div className="results">
          <article className="rcard reveal">
            <div className="rcard-top">
              <div>
                <h3>Reservoir storage</h3>
                <p className="muted">Next-day error in TMC, lower is better. Baseline = "tomorrow same as today".</p>
              </div>
              <div className="big-stat"><b>{beats}/4</b><span>beat the baseline</span></div>
            </div>
            <Legend items={[['LSTM', MODEL], ['Baseline', BASE]]} />
            <ResponsiveContainer width="100%" height={230}>
              <BarChart data={res} margin={{ top: 8, right: 4, left: -14, bottom: 0 }} barGap={3}>
                <CartesianGrid {...grid} />
                <XAxis dataKey="name" {...axis} />
                <YAxis {...axis} />
                <Tooltip cursor={cursor} content={<ChartTip unit=" TMC" digits={3} />} />
                <Bar dataKey="lstm_mae" name="LSTM" fill={MODEL} radius={[5, 5, 0, 0]} maxBarSize={30} />
                <Bar dataKey="persist_mae" name="Baseline" fill={BASE} radius={[5, 5, 0, 0]} maxBarSize={30} />
              </BarChart>
            </ResponsiveContainer>
            <p className="rcard-foot">Trick that helped: predict the <b>change</b> in storage, then add it to today's level.</p>
          </article>

          <article className="rcard reveal">
            <div className="rcard-top">
              <div>
                <h3>Daily rainfall, 12 towns</h3>
                <p className="muted">3-year blind test (2023–25), error in mm/day. Baseline = average for that time of year.</p>
              </div>
              <div className="big-stat"><b>{wins}/12</b><span>towns better</span></div>
            </div>
            <Legend items={[['LSTM', MODEL], ['Baseline', BASE]]} />
            <ResponsiveContainer width="100%" height={230}>
              <BarChart data={towns} margin={{ top: 8, right: 4, left: -14, bottom: 30 }} barGap={1}>
                <CartesianGrid {...grid} />
                <XAxis dataKey="name" {...axis} interval={0} angle={-40} textAnchor="end" height={40} fontSize={11} />
                <YAxis {...axis} />
                <Tooltip cursor={cursor} content={<ChartTip unit=" mm" digits={2} />} />
                <Bar dataKey="lstm" name="LSTM" fill={MODEL} radius={[4, 4, 0, 0]} maxBarSize={14} />
                <Bar dataKey="base" name="Baseline" fill={BASE} radius={[4, 4, 0, 0]} maxBarSize={14} />
              </BarChart>
            </ResponsiveContainer>
            <p className="rcard-foot">Overall error <b>{gain.toFixed(1)}% lower</b> than the baseline, but it still misses the biggest downpours.</p>
          </article>
        </div>

        <div className="lesson reveal">
          <div className="lesson-n">R² {kabini.lstm_r2.toFixed(2)}</div>
          <p>
            Kabini's model scores an R² of {kabini.lstm_r2.toFixed(2)} and is still <b>{(kabini.lstm_mae / kabini.persist_mae).toFixed(1)}× worse</b> than
            just guessing "same as yesterday". The lesson I took away: a high R² isn't a useful forecast. Always check against a simple baseline.
          </p>
        </div>
      </div>
    </section>
  )
}
