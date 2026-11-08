"""NSE Algo Terminal backend bootstrap. No live orders are enabled here."""
import os
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

app = FastAPI(title="NSE Algo Terminal API", version="0.1.0")

# Development-only local frontend origins. Replace with the private production
# dashboard origin before deployment; never use wildcard CORS with credentials.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5500",
        "http://127.0.0.1:5500",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "Authorization"],
)


@app.get("/health")
def health():
    return {"status": "ok", "service": "nse-algo-terminal-api"}


@app.get("/readiness")
def readiness():
    """Reports whether server-side Kite credentials are configured, not their values."""
    configured = bool(os.getenv("KITE_API_KEY") and os.getenv("KITE_API_SECRET"))
    return {
        "status": "configuration_present" if configured else "awaiting_kite_api_credentials",
        "kite_credentials_configured": configured,
        "live_trading_enabled": False,
        "note": "No broker login, market feed, or order execution is enabled in this starter.",
    }
