import data from '../data/projectData.json'

const BUILT_WITH = ['PyTorch', 'TensorFlow', 'scikit-learn', 'Open-Meteo', 'React']

// Grey area chart of 35 years of basin rainfall, standing in for the reference's photo.
function RainPanel() {
  const rows = data.rainfall.era5_annual
  const W = 520, H = 220, pad = 12
  const max = Math.max(...rows.map((r) => r.total)) * 1.05
  const x = (i) => pad + (i / (rows.length - 1)) * (W - pad * 2)
  const y = (v) => H - (v / max) * (H - 30)
  const line = rows.map((r, i) => `${i ? 'L' : 'M'}${x(i).toFixed(1)},${y(r.total).toFixed(1)}`).join(' ')
  const monsoon = rows.map((r, i) => `${i ? 'L' : 'M'}${x(i).toFixed(1)},${y(r.monsoon).toFixed(1)}`).join(' ')
  return (
    <div className="hero-panel">
      <svg viewBox={`0 0 ${W} ${H}`} preserveAspectRatio="none" aria-label="Annual rainfall 1991 to 2025">
        <defs>
          <linearGradient id="hp" x1="0" x2="0" y1="0" y2="1">
            <stop offset="0" stopColor="#ffffff" stopOpacity="0.28" />
            <stop offset="1" stopColor="#ffffff" stopOpacity="0" />
          </linearGradient>
        </defs>
        {[0.25, 0.5, 0.75].map((f) => <line key={f} x1="0" x2={W} y1={H * f} y2={H * f} stroke="#ffffff" strokeOpacity="0.06" />)}
        <path d={`${line} L${x(rows.length - 1)},${H} L${x(0)},${H} Z`} fill="url(#hp)" />
        <path d={line} fill="none" stroke="#e9e9e9" strokeWidth="2" />
        <path d={monsoon} fill="none" stroke="#8a8a8a" strokeWidth="1.5" strokeDasharray="4 4" />
      </svg>
      <div className="hero-panel-cap">
        <b>35 years of rain</b>
        <span>Basin-average rainfall 1991–2025 (solid) and monsoon share (dashed)</span>
      </div>
      <a className="btn-lime hero-panel-btn" href="#allocation">Try the simulator <span aria-hidden="true">→</span></a>
    </div>
  )
}

export default function Hero() {
  const supply = data.allocation.cases.model_based.supply_tmc
  return (
    <header className="hero">
      <div className="container">
        <p className="eyebrow">Personal ML project · Cauvery basin, Karnataka <span /></p>
        <h1 className="hero-title">Predicting Rain To</h1>
        <div className="hero-row">
          <h1 className="hero-title lime" aria-hidden="true">Share Water<span className="dot">.</span></h1>
          <p className="hero-sub">
            LSTMs forecast daily rainfall at 12 Western Ghats towns and next-day storage in 4 Karnataka reservoirs.
            Then 7 strategies decide how the water is shared between Bengaluru, other towns, the river and farms.
          </p>
        </div>
        <div className="hero-grid">
          <RainPanel />
          <ul className="hero-facts">
            <li><b>12</b><span>rain towns</span></li>
            <li><b>4</b><span>reservoirs</span></li>
            <li><b>7</b><span>sharing rules</span></li>
            <li><b>{supply.toFixed(1)}</b><span>TMC forecast</span></li>
          </ul>
        </div>
        <div className="built-row">
          <p>Built with</p>
          <div>{BUILT_WITH.map((b) => <span key={b}>{b}</span>)}</div>
        </div>
      </div>
    </header>
  )
}
