# NSE Algo Terminal backend

FastAPI backend for a read-only Zerodha Kite Connect market-data integration.

## Implemented
- Secure server-side Kite login redirect: `/kite/login`.
- Callback exchange: `/kite/callback`; access token never appears in API responses.
- Session status: `/kite/session/status`.
- Readiness and health checks.
- Daily NFO instrument-master download/cache.
- Read-only near-ATM index option-chain quote snapshot: `/market/option-chain?underlying=NIFTY`.
- Supports NIFTY, BANKNIFTY, FINNIFTY and MIDCPNIFTY; nearest expiry by default, or pass `expiry=YYYY-MM-DD`.
- Uses Kite quotes for LTP, OI, volume and top bid/ask where provided.
- No order placement and no live WebSocket streaming yet.

## Local setup
1. Install Python 3.11+ and run `pip install -r requirements.txt`.
2. Copy `.env.example` to `.env`.
3. Put API key and secret only in the private local environment file / hosting secret manager. Never commit or share them.
4. For local testing, the app Redirect URL must be `http://127.0.0.1:8000/kite/callback`.
5. Run `uvicorn app.main:app --host 127.0.0.1 --port 8000` from this folder.
6. Open `http://127.0.0.1:8000/kite/login`, complete Zerodha login, then test `/market/option-chain?underlying=NIFTY`.

## Deployment and safety
- This development starter stores the access token in process memory only; a restart clears it and daily login is required.
- Before cloud deployment, verify current Zerodha/NSE retail-algo hosting and static-IP requirements. Use approved hosting, HTTPS, restricted access and a proper secret manager.
- Do not expose the API publicly without authentication/rate limiting. Do not put API credentials in frontend HTML, GitHub, browser storage or chat.
- Quote snapshot endpoint is read-only. No live order API exists.
- Historical candles are distinct from historical full option-chain snapshots. Archive only data permitted by the broker/data licence, and do not claim old chain snapshots that were not saved.

## Next work
1. Add WebSocket tick streaming and a secured browser feed.
2. Add snapshot persistence with timestamped archive.
3. Add paper-trading execution, fill simulation and risk controls.
4. Validate disconnect/reconnect and order reconciliation before considering any live order capability.
