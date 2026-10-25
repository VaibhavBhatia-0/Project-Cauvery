// Small shared pieces: chart tooltip, legend, axis styling.

export function ChartTip({ active, payload, label, unit = '', digits = 2, labelFmt }) {
  if (!active || !payload?.length) return null
  return (
    <div className="tip">
      <div className="tip-label">{labelFmt ? labelFmt(label) : label}</div>
      {payload.map((p) => (
        <div key={p.dataKey} className="tip-row">
          <span className="sw" style={{ background: p.color || p.fill }} />
          <span>{p.name}</span>
          <b>{typeof p.value === 'number' ? p.value.toFixed(digits) : p.value}{unit}</b>
        </div>
      ))}
    </div>
  )
}

export function Legend({ items }) {
  return (
    <div className="legend">
      {items.map(([label, color, dashed]) => (
        <span key={label}>
          <i className={dashed ? 'dashed' : ''} style={{ background: dashed ? 'none' : color, borderColor: color }} />
          {label}
        </span>
      ))}
    </div>
  )
}

export const axis = { stroke: '#2a2a2a', tick: { fill: '#8a8a8a', fontSize: 12 }, tickLine: false }
export const grid = { stroke: '#1c1c1c', vertical: false }
export const cursor = { fill: 'rgba(198,244,50,0.05)' }
