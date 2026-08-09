"""
main.py — FastAPI application entrypoint for MandiMind.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="MandiMind API",
    description="Agricultural decision-support agent powered by Gemma 4 and Government of India mandi data.",
    version="0.1.0",
)

# Allow Vite dev server (localhost:5173) during development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health():
    return {"status": "ok", "service": "MandiMind API"}


# TODO: Add routers for:
# - /api/prices   → direct mandi price lookup
# - /api/compare  → full market comparison pipeline
# - /api/chat     → Gemma 4 agent conversational endpoint
