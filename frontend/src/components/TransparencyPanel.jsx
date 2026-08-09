import { useState } from 'react'

const fmt = (n) => n != null ? `₹${Number(n).toLocaleString('en-IN', { maximumFractionDigits: 2 })}` : '—'

export default function TransparencyPanel({ pipelineResult, quantity }) {
  const [open, setOpen] = useState(false)
  if (!pipelineResult?.top_recommendation) return null

  const top = pipelineResult.top_recommendation
  const rate = 0.6 // matches config default

  return (
    <div className="transparency-card">
      <button
        id="transparency-toggle"
        className="transparency-toggle"
        onClick={() => setOpen(o => !o)}
        aria-expanded={open}
      >
        <span>🔬 How was this calculated?</span>
        <span className={`transparency-arrow ${open ? 'open' : ''}`}>▼</span>
      </button>

      {open && (
        <div className="transparency-body">
          <div className="calc-row">
            <span className="calc-label">Government modal price</span>
            <span className="calc-value">{fmt(top.modal_price)}/quintal</span>
          </div>
          <div className="calc-row">
            <span className="calc-label">Quantity</span>
            <span className="calc-value">{quantity} quintals</span>
          </div>
          <div className="calc-row">
            <span className="calc-label">Gross value ({quantity} × ₹{Number(top.modal_price).toLocaleString('en-IN')})</span>
            <span className="calc-value">{fmt(top.gross_value)}</span>
          </div>
          <div className="calc-row">
            <span className="calc-label">Approximate distance</span>
            <span className="calc-value">{top.distance_km?.toFixed(1)} km (straight-line)</span>
          </div>
          <div className="calc-row">
            <span className="calc-label">Estimated transport cost</span>
            <span className="calc-value">− {fmt(top.estimated_transport_cost)}</span>
          </div>
          <div className="calc-row">
            <span className="calc-label">Estimated net return</span>
            <span className="calc-value green">{fmt(top.estimated_net_return)}</span>
          </div>

          <div className="disclaimer-box">
            ⚠️ Transport cost is estimated at ₹{rate}/quintal/km (prototype rate).
            Actual costs depend on vehicle type, route, and local rates.
            Distances shown are straight-line (Haversine), not driving distance.
            All prices sourced from the Government of India Open Data Platform and reflect
            the most recent available data.
          </div>
        </div>
      )}
    </div>
  )
}
