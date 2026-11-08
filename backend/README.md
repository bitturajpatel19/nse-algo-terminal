# NSE Algo Terminal backend starter

This is the secure server-side starting point for the Zerodha Kite Connect integration. The GitHub Pages frontend remains a preview; it must not call Kite with secrets from browser code.

## What this starter does
- Defines the backend runtime and environment variables.
- Provides a health endpoint and configuration readiness check.
- Reserves the server-side integration boundary for Kite Connect.
- Does **not** place orders or expose credentials yet.

## Local setup
1. Install Python 3.11 or newer.
2. From this folder create a virtual environment: `python -m venv .venv`.
3. Activate it and install: `pip install -r requirements.txt`.
4. Copy `.env.example` to `.env` and fill in your Kite API key/secret locally.
5. Run: `uvicorn app.main:app --reload`.
6. Open `http://127.0.0.1:8000/health`.

Never commit `.env`, API secrets, request tokens, access tokens, PINs or TOTP seeds. Do not paste them into chat. Use a secret manager for hosted deployment.

## Next implementation steps
1. Implement Kite login redirect and request-token exchange on the backend only.
2. Store access tokens securely and handle the daily login/token expiry.
3. Fetch the NSE instrument master and build a symbol/token lookup.
4. Connect Kite WebSocket and publish normalized ticks to the dashboard.
5. Add historical candle retrieval, paper execution, order-state reconciliation and risk controls.
6. Enable live orders only after end-to-end paper tests and current broker/exchange compliance checks.

## Data scope
Use only the market data and depth actually exposed by the user's Kite Connect subscription/API. This starter does not claim to provide full historical tick-by-tick order-book archives.
