import { useState, useMemo } from 'react'

const fmt    = (n) => n != null ? `₹${Number(n).toLocaleString('en-IN', { maximumFractionDigits: 0 })}` : '—'
const fmtKm  = (n) => n != null ? `${Number(n).toFixed(1)} km` : '—'
const fmtPrc = (n) => n != null ? `₹${Number(n).toLocaleString('en-IN')}` : '—'

export default function ComparisonTable({ markets, commodity, quantity }) {
  const [sortKey, setSortKey] = useState('estimated_net_return')
  const [sortDir, setSortDir] = useState('desc')

  const sortedMarkets = useMemo(() => {
    if (!markets) return []
    return [...markets].sort((a, b) => {
      let aVal = a[sortKey] ?? 0
      let bVal = b[sortKey] ?? 0
      
      if (typeof aVal === 'string') aVal = aVal.toLowerCase()
      if (typeof bVal === 'string') bVal = bVal.toLowerCase()
      
      if (aVal < bVal) return sortDir === 'asc' ? -1 : 1
      if (aVal > bVal) return sortDir === 'asc' ? 1 : -1
      return 0
    })
  }, [markets, sortKey, sortDir])

  if (!markets || markets.length === 0) return null

  const handleSort = (key) => {
    if (sortKey === key) {
      setSortDir(sortDir === 'asc' ? 'desc' : 'asc')
    } else {
      setSortKey(key)
      // Default to ascending for Distance (lower is better), descending for others (higher is better)
      setSortDir(key === 'distance_km' || key === 'estimated_transport_cost' ? 'asc' : 'desc')
    }
  }

  const renderSortIcon = (key) => {
    if (sortKey !== key) return <span className="sort-icon inactive">↕</span>
    return <span className="sort-icon active">{sortDir === 'asc' ? '↑' : '↓'}</span>
  }

  return (
    <div className="table-card">
      <div className="table-header">
        <div>
          <div className="table-title">Market Comparison</div>
          <div className="table-subtitle">
            {commodity} · {quantity} quintals
          </div>
        </div>
        <span className="badge">{markets.length} markets</span>
      </div>
      <div className="table-scroll">
        <table>
          <thead>
            <tr>
              <th>#</th>
              <th className="sortable" onClick={() => handleSort('market')}>
                Market {renderSortIcon('market')}
              </th>
              <th className="sortable" onClick={() => handleSort('district')}>
                District {renderSortIcon('district')}
              </th>
              <th className="sortable" onClick={() => handleSort('modal_price')}>
                Modal Price {renderSortIcon('modal_price')}
              </th>
              <th className="sortable" onClick={() => handleSort('distance_km')}>
                Distance {renderSortIcon('distance_km')}
              </th>
              <th className="sortable" onClick={() => handleSort('estimated_transport_cost')}>
                Transport {renderSortIcon('estimated_transport_cost')}
              </th>
              <th className="sortable" onClick={() => handleSort('estimated_net_return')}>
                Net Return {renderSortIcon('estimated_net_return')}
              </th>
            </tr>
          </thead>
          <tbody>
            {sortedMarkets.map((m, i) => (
              <tr key={`${m.market}-${i}`} className={i === 0 ? 'top-row' : ''}>
                <td>
                  <span className={`rank-badge ${i === 0 ? 'rank-1' : ''}`}>
                    {i === 0 ? '★' : i + 1}
                  </span>
                </td>
                <td className="market-name">{m.market}</td>
                <td>{m.district}</td>
                <td>{fmtPrc(m.modal_price)}/q</td>
                <td>{fmtKm(m.distance_km)}</td>
                <td>{fmt(m.estimated_transport_cost)}</td>
                <td className={i === 0 ? 'net-return' : 'net-return-dim'}>
                  {fmt(m.estimated_net_return)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
