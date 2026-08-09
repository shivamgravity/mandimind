# MandiMind 🌾🤖

> **An Agentic AI decision-support platform empowering Indian farmers to maximize their crop profits through real-time mandi data, distance optimization, and intelligent market comparison.**

---

## 🏆 The Problem
Indian farmers often lack access to comprehensive, real-time data regarding the most profitable markets (Mandis) to sell their produce. A local mandi might be closer, but a mandi 40 km away might offer a significantly higher modal price that easily offsets the transportation cost. 

Without a way to instantly compare **Modal Price vs. Distance vs. Transport Cost**, farmers risk losing substantial net revenue on every harvest.

## 🚀 The Solution: MandiMind
MandiMind is a full-stack, Agentic AI platform powered by **Gemma 4**. It acts as a smart agricultural advisor. A farmer simply inputs their crop, quantity, and location. MandiMind autonomously:
1. Fetches real-time Government of India mandi prices.
2. Resolves market geographic coordinates.
3. Calculates Haversine distances to candidate markets.
4. Estimates prototype transportation costs based on distance and quantity.
5. Computes the estimated net return for every market.
6. Returns a natural language recommendation and an interactive comparison table.

---

## ✨ Key Features
- **Agentic Reasoning:** Powered by `gemma-4-26b-a4b-it` via the Google GenAI SDK. The AI acts as the orchestrator, intelligently calling Python backend tools to perform complex data gathering.
- **Strict Data Provenance:** The LLM is strictly constrained via XML parsing (`<reply>`) and positive prompt enforcement. It **never** hallucinates prices; it relies 100% on deterministic Python calculations and government data.
- **Smart State-Wide Fallback:** If a farmer's local district has no mandi data for a specific crop today, the pipeline automatically falls back to a state-wide search and ranks the closest alternative districts.
- **Premium Dashboard UI:** A custom React frontend featuring a dark-mode glassmorphic aesthetic, dynamic progress steppers, and fully interactive, sortable data tables.

## 🛠️ Tech Stack
* **Frontend:** React, Vite, Vanilla CSS (Custom Design System)
* **Backend:** Python, FastAPI, Uvicorn
* **AI & Orchestration:** Google GenAI SDK, Gemma 4 (`gemma-4-26b-a4b-it`), Function Calling (Tool Use)
* **Data Sources:** Government of India Open Data Platform (Mocked API layer for hackathon stability)

---

## 🏗️ Architecture

### 1. The Agentic Loop
Unlike simple RAG applications, MandiMind uses a true agentic loop. 
- The user prompt goes to Gemma.
- Gemma recognizes it needs data and outputs a **Tool Call** (e.g., `rank_market_options`).
- The Python FastAPI backend executes the tool and returns the deterministic JSON output.
- Gemma analyzes the JSON and outputs a final, structured natural language recommendation.

### 2. Hackathon Trade-off: The Geocoding Cache
*Note for Judges:* To ensure a completely stable, zero-latency demo without hitting external API rate limits over hackathon Wi-Fi, we implemented an in-memory **Geocoding Cache** (`market_locations.csv`). This maps roughly 100 major APMC markets in UP and MP to static GPS coordinates. In a production environment, this module is designed to be effortlessly swapped with a live Google Maps Geocoding or PostGIS integration.

---

## 💻 Local Setup & Installation

### Prerequisites
- Node.js (v18+)
- Python (3.10+)
- `GEMINI_API_KEY`

### 1. Backend Setup
```bash
# Navigate to project directory
cd mandimind

# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r backend/requirements.txt

# Set your API Key
export GEMINI_API_KEY="your_api_key_here"

# Start the FastAPI server
PYTHONPATH=. uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

### 2. Frontend Setup
```bash
# Open a new terminal and navigate to frontend
cd mandimind/frontend

# Install dependencies
npm install

# Start the Vite development server
npm run dev
```

Visit `http://localhost:5173` to interact with MandiMind!

---
*Built with ❤️ for the Hackathon.*
