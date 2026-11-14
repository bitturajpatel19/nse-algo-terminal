"""NSE Algo Terminal API: Kite login and read-only option-chain quotes.

No order placement is implemented. Tokens stay server-side in process memory.
"""
import asyncio
import hmac
import os
from datetime import date
from pathlib import Path
from threading import Lock
from typing import Any

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, RedirectResponse
from kiteconnect import KiteConnect, KiteTicker

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

app = FastAPI(title="NSE Algo Terminal API", version="0.3.0")

# Production browser origins must be explicitly configured. An empty list is
# safer than allowing arbitrary websites to call this backend.
_allowed_origins = [
    origin.strip().rstrip("/")
    for origin in os.getenv("ALLOWED_ORIGINS", "").split(",")
    if origin.strip()
]
if os.getenv("APP_ENV", "development").lower() != "production":
    _allowed_origins.extend([
        "http://localhost:3000", "http://127.0.0.1:3000",
        "http://localhost:5500", "http://127.0.0.1:5500",
    ])

app.add_middleware(
    CORSMiddleware,
    allow_origins=sorted(set(_allowed_origins)),
    allow_credentials=False,
    allow_methods=["GET"],
    allow_headers=["Content-Type", "Authorization"],
)

_token_lock = Lock()
_kite_access_token: str | None = None
_kite_user_id: str | None = None
_instrument_lock = Lock()
_nfo_instruments: list[dict[str, Any]] = []
_instrument_loaded_on: date | None = None

SPOT_SYMBOLS = {
    "NIFTY": "NSE:NIFTY 50",
    "BANKNIFTY": "NSE:NIFTY BANK",
    "FINNIFTY": "NSE:NIFTY FIN SERVICE",
    "MIDCPNIFTY": "NSE:NIFTY MID SELECT",
}


def _kite_client(authenticated: bool = True) -> KiteConnect:
    api_key = os.getenv("KITE_API_KEY", "").strip()
    if not api_key:
        raise HTTPException(status_code=503, detail="KITE_API_KEY is not configured on the backend")
    kite = KiteConnect(api_key=api_key)
    if authenticated:
        with _token_lock:
            token = _kite_access_token
        if not token:
            raise HTTPException(status_code=401, detail="Kite session is not connected. Open /kite/login first.")
        kite.set_access_token(token)
    return kite


def _load_nfo_instruments(kite: KiteConnect) -> list[dict[str, Any]]:
    global _nfo_instruments, _instrument_loaded_on
    today = date.today()
    with _instrument_lock:
        if _nfo_instruments and _instrument_loaded_on == today:
            return _nfo_instruments
    try:
        rows = kite.instruments("NFO")
    except Exception:
        raise HTTPException(status_code=502, detail="Could not download NFO instrument master from Kite")
    with _instrument_lock:
        _nfo_instruments = rows
        _instrument_loaded_on = today
        return _nfo_instruments


def _quote_chunks(kite: KiteConnect, keys: list[str]) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    # Kite quote accepts a bounded number of instruments per request.
    for start in range(0, len(keys), 200):
        batch = keys[start:start + 200]
        if not batch:
            continue
        try:
            result.update(kite.quote(*batch))
        except Exception:
            # Preserve partial data if a particular batch has a stale/invalid symbol.
            continue
    return result


@app.get("/health")
def health():
    return {"status": "ok", "service": "nse-algo-terminal-api", "version": "0.3.0"}


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
        "market_data_enabled": authenticated,
        "live_trading_enabled": False,
    }


@app.get("/kite/login")
def kite_login():
    return RedirectResponse(url=_kite_client(authenticated=False).login_url(), status_code=302)


@app.get("/kite/callback", response_class=HTMLResponse)
def kite_callback(
    request_token: str | None = Query(default=None),
    status: str | None = Query(default=None),
):
    global _kite_access_token, _kite_user_id
    if status == "error":
        raise HTTPException(status_code=400, detail="Kite login was cancelled")
    if not request_token:
        raise HTTPException(status_code=400, detail="Missing request_token; start at /kite/login")
    secret = os.getenv("KITE_API_SECRET", "").strip()
    if not secret:
        raise HTTPException(status_code=503, detail="KITE_API_SECRET is not configured on the backend")
    try:
        session = _kite_client(authenticated=False).generate_session(request_token, api_secret=secret)
    except Exception:
        raise HTTPException(status_code=401, detail="Kite authentication failed; retry login")
    with _token_lock:
        _kite_access_token = session["access_token"]
        _kite_user_id = session.get("user_id")
    return HTMLResponse(
        "<h2>Kite login successful</h2><p>Backend session connected. You can close this tab.</p>"
        "<p>Read-only market quotes are available. Order placement is disabled.</p>"
    )


@app.get("/kite/session/status")
def kite_session_status():
    with _token_lock:
        return {"authenticated": bool(_kite_access_token), "user_id": _kite_user_id,
                "access_token_exposed": False, "live_trading_enabled": False}


@app.get("/market/option-chain")
def option_chain(
    underlying: str = Query(default="NIFTY"),
    expiry: str | None = Query(default=None, description="YYYY-MM-DD; omit for nearest expiry"),
    strikes_each_side: int = Query(default=10, ge=1, le=30),
):
    """Read-only near-ATM option chain from current Kite quotes and NFO instruments."""
    name = underlying.strip().upper()
    requested_expiry = None
    if expiry:
        try:
            requested_expiry = date.fromisoformat(expiry)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid expiry format. Use YYYY-MM-DD.")
    if name not in SPOT_SYMBOLS:
        raise HTTPException(status_code=400, detail="Supported index underlyings: NIFTY, BANKNIFTY, FINNIFTY, MIDCPNIFTY")
    kite = _kite_client()
    instruments = _load_nfo_instruments(kite)
    try:
        spot_quote = kite.quote(SPOT_SYMBOLS[name]).get(SPOT_SYMBOLS[name], {})
    except Exception:
        spot_quote = {}
    spot = (spot_quote.get("last_price") or spot_quote.get("ohlc", {}).get("close"))
    if spot is None:
        raise HTTPException(status_code=502, detail="Spot quote unavailable from Kite")
    contracts = [
        x for x in instruments
        if x.get("name") == name and x.get("instrument_type") in ("CE", "PE")
        and x.get("expiry") and x.get("expiry") >= date.today()
    ]
    expiries = sorted({x["expiry"] for x in contracts})
    if not expiries:
        raise HTTPException(status_code=404, detail="No active option contracts found in current NFO instrument master")
    chosen_expiry = requested_expiry or expiries[0]
    if chosen_expiry not in expiries:
        raise HTTPException(status_code=404, detail="Requested expiry is not present in current NFO instrument master")
    expiry_contracts = [x for x in contracts if x["expiry"] == chosen_expiry]
    strikes = sorted({float(x["strike"]) for x in expiry_contracts})
    atm = min(strikes, key=lambda s: abs(s - float(spot)))
    atm_index = strikes.index(atm)
    selected_strikes = strikes[max(0, atm_index - strikes_each_side):atm_index + strikes_each_side + 1]
    selected = [x for x in expiry_contracts if float(x["strike"]) in selected_strikes]
    keys = [f'NFO:{x["tradingsymbol"]}' for x in selected]
    quotes = _quote_chunks(kite, keys)
    rows = []
    by_strike: dict[float, dict[str, Any]] = {}
    for contract in selected:
        key = f'NFO:{contract["tradingsymbol"]}'
        q = quotes.get(key, {})
        depth = q.get("depth", {})
        buy = (depth.get("buy") or [{}])[0]
        sell = (depth.get("sell") or [{}])[0]
        leg = {
            "symbol": contract["tradingsymbol"],
            "instrument_token": contract["instrument_token"],
            "ltp": q.get("last_price"),
            "oi": q.get("oi"),
            "volume": q.get("volume"),
            "bid": buy.get("price"),
            "ask": sell.get("price"),
            "last_quantity": q.get("last_quantity"),
            "updated_at": q.get("timestamp"),
        }
        by_strike.setdefault(float(contract["strike"]), {"strike": float(contract["strike"]), "ce": None, "pe": None})
        by_strike[float(contract["strike"])][contract["instrument_type"].lower()] = leg
    for strike in selected_strikes:
        rows.append(by_strike.get(float(strike), {"strike": float(strike), "ce": None, "pe": None}))
    return {
        "source": "Zerodha Kite Connect",
        "mode": "live_quote_snapshot",
        "underlying": name,
        "spot": spot,
        "expiry": chosen_expiry.isoformat(),
        "available_expiries": [x.isoformat() for x in expiries],
        "atm_strike": atm,
        "strikes_each_side": strikes_each_side,
        "rows": rows,
        "as_of": spot_quote.get("timestamp"),
        "note": "Read-only quote snapshot, not a continuous WebSocket stream. OI change, IV and Greeks are not supplied in this response.",
        "data_quality": {
            "missing_call_quotes": sum(1 for row in rows if not row.get("ce") or row["ce"].get("ltp") is None),
            "missing_put_quotes": sum(1 for row in rows if not row.get("pe") or row["pe"].get("ltp") is None),
            "quote_snapshot_only": True,
        },
    }



def _select_stream_contracts(
    instruments: list[dict[str, Any]],
    underlying: str,
    expiry: date,
    spot: float,
    strikes_each_side: int,
) -> list[dict[str, Any]]:
    contracts = [
        item for item in instruments
        if item.get("name") == underlying
        and item.get("instrument_type") in ("CE", "PE")
        and item.get("expiry") == expiry
    ]
    strikes = sorted({float(item["strike"]) for item in contracts})
    if not strikes:
        raise HTTPException(status_code=404, detail="No option contracts found for this expiry")
    atm_index = min(range(len(strikes)), key=lambda index: abs(strikes[index] - spot))
    chosen = set(strikes[max(0, atm_index - strikes_each_side):atm_index + strikes_each_side + 1])
    return [item for item in contracts if float(item["strike"]) in chosen]


@app.websocket("/market/stream")
async def market_stream(
    websocket: WebSocket,
    token: str = Query(..., description="Server-configured stream access token"),
    underlying: str = Query(default="NIFTY"),
    expiry: str | None = Query(default=None, description="YYYY-MM-DD; omit for nearest expiry"),
    strikes_each_side: int = Query(default=10, ge=1, le=30),
):
    """Read-only KiteTicker stream for a selected near-ATM index option chain."""
    expected = os.getenv("STREAM_ACCESS_TOKEN", "").strip()
    if not expected or not hmac.compare_digest(token, expected):
        await websocket.close(code=1008, reason="Stream authentication failed")
        return
    name = underlying.strip().upper()
    if name not in SPOT_SYMBOLS:
        await websocket.close(code=1008, reason="Unsupported underlying")
        return
    requested_expiry = None
    if expiry:
        try:
            requested_expiry = date.fromisoformat(expiry)
        except ValueError:
            await websocket.close(code=1008, reason="Invalid expiry; use YYYY-MM-DD")
            return
    try:
        kite = _kite_client()
        instruments = _load_nfo_instruments(kite)
        spot_quote = kite.quote(SPOT_SYMBOLS[name]).get(SPOT_SYMBOLS[name], {})
        spot = spot_quote.get("last_price") or spot_quote.get("ohlc", {}).get("close")
        if spot is None:
            await websocket.close(code=1011, reason="Spot quote unavailable")
            return
        available = sorted({
            item["expiry"] for item in instruments
            if item.get("name") == name and item.get("instrument_type") in ("CE", "PE")
            and item.get("expiry") and item["expiry"] >= date.today()
        })
        chosen_expiry = requested_expiry or (available[0] if available else None)
        if chosen_expiry not in available:
            await websocket.close(code=1008, reason="Requested expiry unavailable")
            return
        selected = _select_stream_contracts(
            instruments, name, chosen_expiry, float(spot), strikes_each_side
        )
        tokens = sorted({int(item["instrument_token"]) for item in selected})
        if not tokens:
            await websocket.close(code=1008, reason="No contracts selected")
            return
        with _token_lock:
            api_key = os.getenv("KITE_API_KEY", "").strip()
            access_token = _kite_access_token
        if not api_key or not access_token:
            await websocket.close(code=1008, reason="Kite session is not connected")
            return
    except HTTPException as exc:
        await websocket.close(code=1011, reason=str(exc.detail)[:120])
        return
    except Exception:
        await websocket.close(code=1011, reason="Could not prepare market stream")
        return

    await websocket.accept()
    loop = asyncio.get_running_loop()
    queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue(maxsize=2000)
    ticker = KiteTicker(api_key, access_token)

    def on_ticks(_ws, ticks):
        for tick in ticks:
            payload = dict(tick)
            try:
                loop.call_soon_threadsafe(queue.put_nowait, payload)
            except RuntimeError:
                return

    def on_connect(ws, _response):
        ws.subscribe(tokens)
        ws.set_mode(ws.MODE_FULL, tokens)

    def on_error(_ws, code, reason):
        try:
            loop.call_soon_threadsafe(
                queue.put_nowait,
                {"_stream_error": {"code": code, "message": str(reason)}},
            )
        except RuntimeError:
            pass

    ticker.on_ticks = on_ticks
    ticker.on_connect = on_connect
    ticker.on_error = on_error
    try:
        ticker.connect(threaded=True)
        await websocket.send_json({
            "type": "stream_status",
            "status": "connecting",
            "source": "Zerodha KiteTicker",
            "underlying": name,
            "expiry": chosen_expiry.isoformat(),
            "subscribed_instruments": len(tokens),
            "mode": "full",
            "live_trading_enabled": False,
        })
        while True:
            try:
                tick = await asyncio.wait_for(queue.get(), timeout=30)
                await websocket.send_json({"type": "tick", "data": tick})
            except asyncio.TimeoutError:
                await websocket.send_json({"type": "heartbeat", "status": "connected"})
    except WebSocketDisconnect:
        pass
    except Exception:
        try:
            await websocket.close(code=1011, reason="Market stream disconnected")
        except Exception:
            pass
    finally:
        try:
            ticker.close()
        except Exception:
            pass

@app.get("/market/instruments/status")
def instrument_status():
    with _instrument_lock:
        return {"loaded": bool(_nfo_instruments), "count": len(_nfo_instruments),
                "loaded_on": _instrument_loaded_on.isoformat() if _instrument_loaded_on else None}
