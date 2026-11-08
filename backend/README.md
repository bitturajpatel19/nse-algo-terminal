# NSE Algo Terminal backend

Secure server-side foundation for the Zerodha Kite Connect integration.

## Current capabilities
- FastAPI health and readiness endpoints.
- Starts the official Kite login flow at `/kite/login`.
- Handles the callback at `/kite/callback` and exchanges the one-time request token on the server.
- Keeps the access token in process memory; API responses never expose it.
- Does not place orders or stream market data yet.

## Local development setup
1. Install Python 3.11 or newer.
2. From this folder create a virtual environment: `python -m venv .venv`.
3. Activate it and install: `pip install -r requirements.txt`.
4. Copy `.env.example` to `.env`.
5. Add your own Kite API key and secret to the local `.env` file. Never commit it or paste credentials into chat.
6. Confirm the app's Redirect URL is exactly `http://127.0.0.1:8000/kite/callback` for local testing.
7. Run: `uvicorn app.main:app --host 127.0.0.1 --port 8000`.
8. Open `http://127.0.0.1:8000/kite/login` in the same computer's browser and complete the Zerodha login.
9. Check `http://127.0.0.1:8000/kite/session/status`. It reports authentication status but never the access token.

## Important security and deployment notes
- The `.env` file, API key, API secret, request token, access token, PIN and TOTP seed must never be committed to GitHub or pasted into chat.
- This starter keeps the access token only in process memory. Restarting the backend clears it; daily Kite re-authentication is expected.
- Do not deploy this public development starter as-is. Before cloud deployment, confirm the currently applicable Zerodha/NSE hosting, static-IP and retail-algo requirements, use HTTPS, restrict network access, and add secure persistent secret/token handling.
- No live order endpoint exists. Live orders remain disabled until paper testing, order-state reconciliation and compliance checks are complete.

## Next implementation steps
1. Add secure instrument-master download and symbol/token lookup.
2. Add Kite WebSocket market-data service and a dashboard stream.
3. Add historical candle retrieval and permitted snapshot storage.
4. Add paper execution, order-state reconciliation and risk controls.
5. Only then evaluate live order integration under current broker/exchange requirements.

## Data limitations
Use only data and market depth exposed by the user's Kite Connect subscription/API. Historical candles do not recreate a complete historical option chain or tick-by-tick order-book archive.
