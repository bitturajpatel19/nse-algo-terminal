"""NSE Algo Terminal backend: safe Kite Connect login foundation.

No live orders are enabled. Access tokens remain in process memory for this
development starter and are never returned by an API response.
"""
import os
from pathlib import Path
from threading import Lock

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, RedirectResponse
from kiteconnect import KiteConnect

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

app = FastAPI(title="NSE Algo Terminal API", version="0.2.0")

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

_token_lock = Lock()
_kite_access_token: str | None = None
_kite_user_id: str | None = None


def _kite_client() -> KiteConnect:
    api_key = os.getenv("KITE_API_KEY", "").strip()
    if not api_key:
        raise HTTPException(status_code=503, detail="KITE_API_KEY is not configured on the backend")
    return KiteConnect(api_key=api_key)


@app.get("/health")
def health():
    return {"status": "ok", "service": "nse-algo-terminal-api"}


@app.get("/readiness")
def readiness():
    configured = bool(os.getenv("KITE_API_KEY") and os.getenv("KITE_API_SECRET"))
    with _token_lock:
        authenticated = bool(_kite_access_token)
    return {
        "status": "authenticated" if authenticated else (
            "configuration_present" if configured else "awaiting_kite_api_credentials"
        ),
        "kite_credentials_configured": configured,
        "kite_authenticated": authenticated,
        "live_trading_enabled": False,
        "market_data_enabled": False,
        "note": "Login foundation only; no market feed or order execution is enabled yet.",
    }


@app.get("/kite/login")
def kite_login():
    """Start the official Kite login flow; secrets stay on this backend."""
    kite = _kite_client()
    return RedirectResponse(url=kite.login_url(), status_code=302)


@app.get("/kite/callback", response_class=HTMLResponse)
def kite_callback(
    request_token: str | None = Query(default=None),
    status: str | None = Query(default=None),
):
    """Exchange the one-time request token server-side; never expose tokens to browser UI."""
    global _kite_access_token, _kite_user_id
    if status == "error":
        raise HTTPException(status_code=400, detail="Kite login was cancelled")
    if not request_token:
        raise HTTPException(status_code=400, detail="Missing Kite request_token; start at /kite/login")
    api_secret = os.getenv("KITE_API_SECRET", "").strip()
    if not api_secret:
        raise HTTPException(status_code=503, detail="KITE_API_SECRET is not configured on the backend")
    try:
        session = _kite_client().generate_session(request_token, api_secret=api_secret)
    except Exception:
        # Do not return broker error payloads or request tokens to the browser.
        raise HTTPException(status_code=401, detail="Kite authentication failed; retry login")
    with _token_lock:
        _kite_access_token = session["access_token"]
        _kite_user_id = session.get("user_id")
    return HTMLResponse(
        "<h2>Kite login successful</h2>"
        "<p>Your backend session is connected. You can close this tab.</p>"
        "<p>Market data and order placement are not enabled yet.</p>"
    )


@app.get("/kite/session/status")
def kite_session_status():
    with _token_lock:
        return {
            "authenticated": bool(_kite_access_token),
            "user_id": _kite_user_id,
            "access_token_exposed": False,
            "live_trading_enabled": False,
        }
