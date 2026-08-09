const fmt = (n) => n != null ? `₹${Number(n).toLocaleString('en-IN', { maximumFractionDigits: 0 })}` : '—'
const fmtKm = (n) => n != null ? `${Number(n).toFixed(1)} km` : '—'

export default function RecommendationCard({ market, fallbackUsed, candidatesCount }) {
  if (!market) return null

  return (
    <div className="rec-card">
      {fallbackUsed && (
        <div className="fallback-badge">
          ⚡ State-wide search used — no local listing found
        </div>
      )}

      <div className="rec-label">🏆 Recommended Market</div>
      <div className="rec-market">{market.market}</div>
      <div className="rec-district">{market.district}, {market.state}</div>

      <div className="rec-return">{fmt(market.estimated_net_return)}</div>
      <div className="rec-return-label">Estimated Net Return</div>

      <div className="rec-stats">
        <div className="rec-stat">
          <div className="rec-stat-label">Modal Price</div>
          <div className="rec-stat-value">₹{Number(market.modal_price).toLocaleString('en-IN')}/q</div>
        </div>
        <div className="rec-stat">
          <div className="rec-stat-label">Distance</div>
          <div className="rec-stat-value">{fmtKm(market.distance_km)}</div>
        </div>
        <div className="rec-stat">
          <div className="rec-stat-label">Transport</div>
          <div className="rec-stat-value">{fmt(market.estimated_transport_cost)}</div>
        </div>
      </div>

      {candidatesCount > 1 && (
        <p style={{fontSize:'0.78rem',color:'var(--text-dim)',marginTop:'16px'}}>
          Best among {candidatesCount} market{candidatesCount > 1 ? 's' : ''} considered within the search radius.
        </p>
      )}
    </div>
  )
}
