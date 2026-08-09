import { useState } from 'react'
import axios from 'axios'

import Header           from './components/Header'
import QueryForm        from './components/QueryForm'
import ProgressSteps    from './components/ProgressSteps'
import RecommendationCard from './components/RecommendationCard'
import ComparisonTable  from './components/ComparisonTable'
import GemmaReply       from './components/GemmaReply'
import TransparencyPanel from './components/TransparencyPanel'
import DataProvenance   from './components/DataProvenance'

// Initial step states
const INITIAL_STEPS = {
  understanding:  'pending',
  prices:         'pending',
  fallback:       'skipped',
  locations:      'pending',
  distance:       'pending',
  transport:      'pending',
  returns:        'pending',
  recommendation: 'pending',
}

export default function App() {
  const [loading, setLoading]             = useState(false)
  const [steps, setSteps]                 = useState(INITIAL_STEPS)
  const [result, setResult]               = useState(null)   // pipeline_result
  const [reply, setReply]                 = useState('')
  const [toolCalls, setToolCalls]         = useState([])
  const [error, setError]                 = useState(null)
  const [lastQuery, setLastQuery]         = useState(null)
  const [showResults, setShowResults]     = useState(false)

  const setStep = (key, status) =>
    setSteps(s => ({ ...s, [key]: status }))

  const handleSubmit = async (formData) => {
    // Reset state
    setLoading(true)
    setError(null)
    setResult(null)
    setReply('')
    setToolCalls([])
    setShowResults(false)
    setLastQuery(formData)
    setSteps(INITIAL_STEPS)

    try {
      // Step 1: understanding
      setStep('understanding', 'active')
      await delay(300)
      setStep('understanding', 'done')

      // Step 2: prices (starts when API call begins)
      setStep('prices', 'active')

      // Build natural language message for the agent
      const message = `I have ${formData.quantity_quintals} quintals of ${formData.commodity} ` +
        `and I am in ${formData.location}, ${formData.state}. ` +
        `Please find the best market to sell within ${formData.search_radius_km} km.`

      // Call /api/chat — this triggers the full agent pipeline
      const response = await axios.post('/api/chat', {
        message,
        history: [],
      })

      const { reply: agentReply, tool_calls_made, pipeline_result } = response.data

      setStep('prices', 'done')

      // Update steps based on what the agent did
      if (pipeline_result) {
        if (pipeline_result.state_wide_fallback_used) {
          setStep('fallback', 'active')
          await delay(200)
          setStep('fallback', 'done')
        } else {
          setStep('fallback', 'skipped')
        }

        setStep('locations', 'active')
        await delay(250)
        setStep('locations', 'done')

        setStep('distance', 'active')
        await delay(200)
        setStep('distance', 'done')

        setStep('transport', 'active')
        await delay(200)
        setStep('transport', 'done')

        setStep('returns', 'active')
        await delay(200)
        setStep('returns', 'done')
      }

      setStep('recommendation', 'active')
      await delay(300)
      setStep('recommendation', 'done')

      setResult(pipeline_result)
      setReply(agentReply)
      setToolCalls(tool_calls_made || [])
      setShowResults(true)

    } catch (err) {
      console.error(err)
      const msg = err.response?.data?.detail || err.message || 'An unexpected error occurred.'
      setError(msg)
      // Mark active steps as error
      setSteps(s => Object.fromEntries(
        Object.entries(s).map(([k, v]) => [k, v === 'active' ? 'error' : v])
      ))
    } finally {
      setLoading(false)
    }
  }

  const pipelineOk = result?.status === 'ok'
  const top = result?.top_recommendation

  return (
    <div className="app-wrapper">
      <Header />

      <main className="main-content">
        <div className="hero">
          <h1>Find Your Best Mandi</h1>
          <p>
            Real Government mandi prices · Gemma 4 AI reasoning ·
            Transport-adjusted net return comparison
          </p>
        </div>

        <div className="grid-2">
          {/* Left column: form + progress */}
          <div>
            <QueryForm onSubmit={handleSubmit} loading={loading} />

            {(loading || showResults) && (
              <div style={{ marginTop: '24px' }}>
                <ProgressSteps steps={steps} />
              </div>
            )}
          </div>

          {/* Right column: results */}
          <div>
            {error && (
              <div className="error-box">
                <span>⚠️</span>
                <div>
                  <strong>Error:</strong> {error}
                </div>
              </div>
            )}

            {!showResults && !loading && !error && (
              <div className="empty-state">
                <div className="empty-icon">🌾</div>
                <div className="empty-title">Ready to analyse</div>
                <div className="empty-desc">
                  Enter your location, crop, and quantity — Gemma 4 will find
                  your best estimated net return across nearby mandis.
                </div>
              </div>
            )}

            {showResults && result?.status === 'no_results' && (
              <div className="error-box" style={{background:'rgba(245,158,11,0.07)',borderColor:'rgba(245,158,11,0.25)',color:'#fcd34d'}}>
                <span>⚠️</span>
                <div>{result.message}</div>
              </div>
            )}

            {showResults && pipelineOk && top && (
              <>
                <RecommendationCard
                  market={top}
                  fallbackUsed={result.state_wide_fallback_used}
                  candidatesCount={result.candidates_in_radius}
                />

                <GemmaReply reply={reply} toolCalls={toolCalls} />

                <ComparisonTable
                  markets={result.ranked_markets}
                  commodity={lastQuery?.commodity}
                  quantity={lastQuery?.quantity_quintals}
                />

                <TransparencyPanel
                  pipelineResult={result}
                  quantity={lastQuery?.quantity_quintals}
                />
              </>
            )}
          </div>
        </div>
      </main>

      <DataProvenance pipelineResult={result} />
    </div>
  )
}

function delay(ms) {
  return new Promise(r => setTimeout(r, ms))
}
