const STEPS = [
  { key: 'understanding',  label: 'Understanding request',          icon: '🧠' },
  { key: 'prices',         label: 'Checking government mandi data', icon: '📊' },
  { key: 'fallback',       label: 'Expanding to nearby markets',    icon: '🔍' },
  { key: 'locations',      label: 'Resolving market coordinates',   icon: '📍' },
  { key: 'distance',       label: 'Calculating distances',          icon: '📏' },
  { key: 'transport',      label: 'Estimating transport costs',     icon: '🚛' },
  { key: 'returns',        label: 'Comparing net returns',          icon: '💰' },
  { key: 'recommendation', label: 'Preparing recommendation',       icon: '✅' },
]

export default function ProgressSteps({ steps }) {
  // steps = { [key]: 'pending' | 'active' | 'done' | 'skipped' }
  return (
    <div className="card progress-card">
      <div className="card-title">Agent Progress</div>
      <div className="progress-steps">
        {STEPS.map(step => {
          const status = steps[step.key] || 'pending'
          if (status === 'skipped') return null
          return (
            <div key={step.key} className="step">
              <div className={`step-icon ${status}`}>
                {status === 'active'  ? '⟳' :
                 status === 'done'    ? '✓' :
                 status === 'error'   ? '✗' :
                 step.icon}
              </div>
              <div className="step-text">
                <div className={`step-label ${status}`}>{step.label}</div>
                {status === 'active' && (
                  <div className="step-detail">Running…</div>
                )}
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
