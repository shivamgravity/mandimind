export default function DataProvenance({ pipelineResult }) {
  const date = new Date().toLocaleDateString('en-IN', {
    day: '2-digit', month: 'short', year: 'numeric'
  })

  return (
    <footer className="provenance">
      <div className="provenance-inner">
        <div className="provenance-source">
          <span className="provenance-flag">🇮🇳</span>
          <div className="provenance-text">
            <strong>Price source:</strong> Government of India Open Government Data Platform<br />
            <span style={{fontSize:'0.72rem'}}>
              Dataset: Current Daily Price of Various Commodities from Various Markets (Mandi) ·
              Ministry of Agriculture &amp; Farmers Welfare
            </span>
          </div>
        </div>
        <div style={{textAlign:'right'}}>
          <div className="provenance-date">Data as of: {date}</div>
          {pipelineResult?.total_api_records > 0 && (
            <div className="provenance-date">
              {pipelineResult.total_api_records} records in today's feed
            </div>
          )}
          <div style={{fontSize:'0.7rem',color:'var(--text-dim)',marginTop:'4px'}}>
            MandiMind is not affiliated with or endorsed by the Government of India.
          </div>
        </div>
      </div>
    </footer>
  )
}
