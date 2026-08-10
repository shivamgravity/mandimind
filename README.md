# MandiMind 🌾🤖

> **An Agentic AI decision-support platform empowering Indian farmers to maximize their crop profits through real-time mandi data, distance optimization, and intelligent market comparison.**

---

## 🏆 The Problem

Indian farmers often lack access to comprehensive, real-time data regarding the most profitable markets (Mandis) to sell their produce. A local mandi might be closer, but a mandi 40 km away might offer a significantly higher modal price that easily offsets the transportation cost.

Without a way to instantly compare **Modal Price vs. Distance vs. Transport Cost**, farmers risk losing substantial net revenue on every harvest.

## 🚀 The Solution: MandiMind

MandiMind is an Agentic AI platform powered by **Gemma 4**, deployed as a single Streamlit application. A farmer simply inputs their crop, quantity, and location. MandiMind autonomously:

1. Fetches real-time Government of India mandi prices.
2. Resolves market geographic coordinates.
3. Calculates Haversine distances to candidate markets.
4. Estimates prototype transportation costs based on distance and quantity.
5. Computes the estimated net return for every market.
6. Returns a natural language recommendation and an interactive comparison table.

---

## ✨ Key Features

- **Agentic Reasoning:** Powered by `gemma-4-26b-a4b-it` via the Google GenAI SDK. The AI acts as the orchestrator, intelligently calling Python backend tools to perform complex data gathering.
- **Strict Data Provenance:** The LLM is strictly constrained — it **never** hallucinates prices. It relies 100% on deterministic Python calculations and live government data.
- **Smart State-Wide Fallback:** If a farmer's local district has no mandi data for a specific crop today, the pipeline automatically falls back to a state-wide search and ranks the closest alternative districts.
- **3-Tab Streamlit UI:** Market Finder, AI Chat (English & Hindi), and a direct Price Lookup panel — all in a single app.

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| **UI** | Streamlit |
| **AI & Orchestration** | Google GenAI SDK, Gemma 4 (`gemma-4-26b-a4b-it`) |
| **Data** | Government of India Open Data Platform (data.gov.in) |
| **Backend logic** | Python, Pydantic, Pandas |

---

## 🏗️ Architecture

### The Agentic Pipeline

```
User Input (location, crop, quantity)
        │
        ▼
  _parse_query()          ← extract intent from natural language
        │
        ▼
  rank_market_options()   ← deterministic Python pipeline:
    ├── get_mandi_prices()      fetch live Gov. of India prices
    ├── get_origin_coordinates() resolve farmer's GPS coordinates
    ├── find_nearby_markets()   filter by search radius (Haversine)
    ├── estimate_transport_cost() ₹ = distance × quantity × rate
    └── calculate_estimated_return() net_return = gross - transport
        │
        ▼
  Gemma 4 LLM             ← single stateless call to summarise
        │
        ▼
  Streamlit UI            ← recommendation card + comparison table
```

### Geocoding Cache

To avoid hitting external geocoding APIs, market GPS coordinates are stored in `data/market_locations.csv` — covering ~100 major APMC markets across UP and MP. In production this module can be swapped for a live Maps/PostGIS integration.

---

## 💻 Local Setup

### Prerequisites
- Python 3.10+
- A `GEMINI_API_KEY` from [Google AI Studio](https://aistudio.google.com/)
- A `DATA_GOV_API_KEY` from [data.gov.in](https://data.gov.in/)

### Installation

```bash
# Clone and enter the project
git clone <your-repo-url>
cd mandimind

# Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy the env template and fill in your keys
cp .env.example .env
# Edit .env and set DATA_GOV_API_KEY and GEMINI_API_KEY

# Run the Streamlit app
streamlit run streamlit_app.py
```

Visit `http://localhost:8501` to interact with MandiMind.

---

## ☁️ Deploying to Streamlit Community Cloud

1. Push this repository to GitHub.
2. Go to [share.streamlit.io](https://share.streamlit.io) → **New app**.
3. Select your repo and set **Main file path** to `streamlit_app.py`.
4. Open **Settings → Secrets** and add:
   ```toml
   DATA_GOV_API_KEY = "your_key_here"
   GEMINI_API_KEY   = "your_key_here"
   ```
5. Click **Deploy** — no additional server configuration needed.

---

## 📁 Project Structure

```
mandimind/
├── streamlit_app.py          # Main Streamlit application
├── requirements.txt          # Python dependencies
├── .env.example              # Environment variable template
├── .streamlit/
│   ├── config.toml           # Dark theme & server config
│   └── secrets.toml.example  # Secrets template for Cloud deploy
├── backend/
│   ├── config.py             # Settings (env + Streamlit secrets)
│   ├── agent/
│   │   ├── gemma_agent.py    # Gemma 4 agentic loop
│   │   ├── prompts.py        # System prompt
│   │   └── schemas.py        # Pydantic data models
│   ├── services/
│   │   ├── pipeline.py       # Full market comparison pipeline
│   │   └── data_gov.py       # data.gov.in API client
│   └── tools/
│       ├── mandi_prices.py   # Price fetching tool
│       ├── market_locations.py # GPS coordinate lookup
│       ├── distance.py       # Haversine distance
│       ├── transport.py      # Transport cost estimator
│       └── returns.py        # Net return calculator
└── data/
    └── market_locations.csv  # APMC market GPS coordinates
```

---

> ⚠️ **Disclaimer:** Transport costs shown are prototype estimates based on a configurable rate (₹/quintal/km) and do not represent official government or logistics rates. Always verify current prices and transport costs locally before making selling decisions.

*Built with ❤️ for the Hackathon.*
