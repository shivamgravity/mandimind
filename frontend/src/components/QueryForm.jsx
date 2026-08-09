import { useState } from 'react'

const CROPS = [
  'Wheat', 'Potato', 'Tomato', 'Onion', 'Rice', 'Maize', 'Mustard',
  'Soyabean', 'Cotton', 'Sugarcane', 'Barley', 'Gram', 'Arhar/Tur',
  'Moong', 'Urad', 'Lentil', 'Groundnut', 'Sunflower Seed',
  'Garlic', 'Ginger', 'Chilli', 'Brinjal', 'Cabbage', 'Cauliflower',
]

const STATES = [
  'Uttar Pradesh', 'Madhya Pradesh', 'Punjab', 'Haryana',
  'Rajasthan', 'Bihar', 'Maharashtra', 'Karnataka',
]

export default function QueryForm({ onSubmit, loading }) {
  const [form, setForm] = useState({
    location: 'Prayagraj',
    commodity: 'Wheat',
    state: 'Uttar Pradesh',
    quantity: '20',
    radius: 150,
  })
  const [errors, setErrors] = useState({})

  const set = (key, val) => setForm(f => ({ ...f, [key]: val }))

  const validate = () => {
    const e = {}
    if (!form.location.trim()) e.location = 'Location is required'
    if (!form.commodity) e.commodity = 'Select a crop'
    const qty = parseFloat(form.quantity)
    if (isNaN(qty) || qty <= 0) e.quantity = 'Enter a valid positive quantity'
    setErrors(e)
    return Object.keys(e).length === 0
  }

  const handleSubmit = (e) => {
    e.preventDefault()
    if (!validate()) return
    onSubmit({
      location: form.location.trim(),
      commodity: form.commodity,
      state: form.state,
      quantity_quintals: parseFloat(form.quantity),
      search_radius_km: form.radius,
    })
  }

  return (
    <div className="card">
      <div className="card-title">Your Query</div>
      <form className="form" onSubmit={handleSubmit} id="query-form">

        <div className="field">
          <label htmlFor="location">Location</label>
          <input
            id="location"
            className="input"
            placeholder="e.g. Prayagraj"
            value={form.location}
            onChange={e => set('location', e.target.value)}
            disabled={loading}
            autoComplete="off"
          />
          {errors.location && <span style={{color:'#f87171',fontSize:'0.78rem'}}>{errors.location}</span>}
        </div>

        <div className="field">
          <label htmlFor="state">State</label>
          <select
            id="state"
            className="select input"
            value={form.state}
            onChange={e => set('state', e.target.value)}
            disabled={loading}
          >
            {STATES.map(s => <option key={s} value={s}>{s}</option>)}
          </select>
        </div>

        <div className="field">
          <label htmlFor="commodity">Crop / Commodity</label>
          <select
            id="commodity"
            className="select input"
            value={form.commodity}
            onChange={e => set('commodity', e.target.value)}
            disabled={loading}
          >
            {CROPS.map(c => <option key={c} value={c}>{c}</option>)}
          </select>
          {errors.commodity && <span style={{color:'#f87171',fontSize:'0.78rem'}}>{errors.commodity}</span>}
        </div>

        <div className="field">
          <label htmlFor="quantity">Quantity</label>
          <div className="input-row">
            <input
              id="quantity"
              className="input"
              type="number"
              min="0.1"
              step="any"
              placeholder="20"
              value={form.quantity}
              onChange={e => set('quantity', e.target.value)}
              disabled={loading}
            />
            <div className="unit-label">Quintals</div>
          </div>
          {errors.quantity && <span style={{color:'#f87171',fontSize:'0.78rem'}}>{errors.quantity}</span>}
        </div>

        <div className="field">
          <label>Search Radius</label>
          <div className="slider-row">
            <input
              id="radius"
              type="range"
              className="slider"
              min="50" max="500" step="25"
              value={form.radius}
              onChange={e => set('radius', Number(e.target.value))}
              disabled={loading}
            />
            <span className="slider-value">{form.radius} km</span>
          </div>
        </div>

        <button
          id="find-market-btn"
          type="submit"
          className={`btn-primary ${loading ? 'loading' : ''}`}
          disabled={loading}
        >
          {loading ? '⏳ Analysing...' : '🔍 Find Best Market'}
        </button>
      </form>
    </div>
  )
}
