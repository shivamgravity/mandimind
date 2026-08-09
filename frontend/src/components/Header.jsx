export default function Header() {
  return (
    <header className="header">
      <div className="header-inner">
        <div className="logo">
          <span className="logo-icon">🌾</span>
          <div>
            <div className="logo-text">MandiMind</div>
            <div className="logo-tagline">From market prices to better selling decisions</div>
          </div>
        </div>
        <div className="header-badges">
          <span className="badge badge-green">
            <span className="badge-dot" />
            Gemma 4 Agent
          </span>
          <span className="badge">🇮🇳 Govt. Data</span>
        </div>
      </div>
    </header>
  )
}
