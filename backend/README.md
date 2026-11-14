# NSE Algo Terminal backend

FastAPI backend for a read-only Zerodha Kite Connect market-data integration.

## Implemented
- Server-side Kite login redirect: `/kite/login`.
- Callback exchange: `/kite/callback`; access token never appears in API responses.
- Session status: `/kite/session/status`.
- Readiness and health checks: `/readiness`, `/health`.
- Daily NFO instrument-master download/cache.
- Read-only near-ATM index option-chain quote snapshot: `/market/option-chain?underlying=NIFTY`.
- Supports NIFTY, BANKNIFTY, FINNIFTY and MIDCPNIFTY; nearest expiry by default, or pass `expiry=YYYY-MM-DD`.
- Kite quotes for LTP, OI, volume and top bid/ask where provided.
- Read-only near-ATM option-chain streaming endpoint at `/market/stream` using KiteTicker full mode; browser access is gated by a server-side `STREAM_ACCESS_TOKEN`.
- No order placement.

## Local development
1. Use Python 3.11+ and install dependencies: `pip install -r requirements.txt`.
2. Copy `.env.example` to `.env`.
3. Put API key and secret only in the private `.env` file or a hosting secret manager. Never commit or share them.
4. In the Kite Developer Console, set the app Redirect URL to the exact callback URL used by your environment. For local testing: `http://127.0.0.1:8000/kite/callback`.
5. Generate a long random `STREAM_ACCESS_TOKEN` and keep it only in the private `.env` / hosting secret manager. Do not use a short or guessable value.
6. Run `uvicorn app.main:app --host 127.0.0.1 --port 8000` from this folder.
7. Open `http://127.0.0.1:8000/kite/login`, complete Zerodha login, then test `/market/option-chain?underlying=NIFTY`.
8. The WebSocket route is `/market/stream?token=...&underlying=NIFTY`; use `ws://127.0.0.1:8000` locally and `wss://YOUR-DOMAIN` behind HTTPS in production. Optional parameters: `expiry=YYYY-MM-DD` and `strikes_each_side=10`.

## Docker deployment preparation
This repository now includes a Dockerfile and Compose configuration. These are deployment foundations, not a claim that a VPS has been provisioned or the service is publicly deployed.

1. Provision a cloud VPS only after selecting a provider/region and confirming a dedicated static public IPv4 address is included.
2. Secure the server first: update packages, use SSH keys, disable password SSH where practical, and configure the provider firewall.
3. Allow inbound SSH only from trusted admin IPs where possible, and allow public HTTPS (443). Do not expose port 8000 publicly.
4. Install Docker Engine and the Docker Compose plugin using the VPS provider's supported instructions.
5. Copy this `backend` directory to the server. Create `.env` from `.env.example`; set `KITE_API_KEY`, `KITE_API_SECRET`, and the exact production `ALLOWED_ORIGINS`. Restrict the file: `chmod 600 .env`.
6. Configure the Kite Developer Console Redirect URL to the public HTTPS callback, for example `https://YOUR-DOMAIN/kite/callback`. The domain must resolve to this VPS and HTTPS must work before completing Kite login.
7. Put a TLS reverse proxy (for example, Caddy or Nginx with a valid certificate) in front of the API and proxy to `127.0.0.1:8000`. The Compose file deliberately binds the API to localhost.
8. Start with `docker compose up -d --build`; inspect with `docker compose ps` and `docker compose logs -f api`. Verify `https://YOUR-DOMAIN/health` and `/readiness`.
9. Register the VPS's fixed public IP in the Kite Developer Console as the primary static IP, following Zerodha's current instructions. If a secondary IP is configured, it must also be a stable IP from which requests can originate.
10. Recheck the redirect URL, HTTPS, firewall, CORS origin and registered static IP before enabling any future order workflow.

Do not publish a public API until authentication, rate limiting, TLS, monitoring and access restrictions are implemented and tested. CORS is not authentication. The WebSocket currently uses a server-side query-string secret because browser WebSocket APIs do not support arbitrary authorization headers; configure reverse-proxy access-log redaction and rotate this secret if exposed. Do not expose the endpoint publicly until TLS, secret redaction, rate limiting and session controls are in place.

## Important runtime limitation
- The current Kite access token is held in process memory. The container intentionally runs one Uvicorn worker; multiple workers would have separate in-memory sessions. A container restart clears the token and daily Kite login is expected.
- Do not scale this in-memory session design across multiple containers. A later phase must add a secure shared session store and operational controls before horizontal scaling.
- Never put API credentials, access tokens, PINs or TOTP seeds in frontend HTML, GitHub, browser storage or chat.
- Quote snapshot endpoint is read-only. No live order API exists.
- Historical candles do not recreate full historical option chains. Archive only data permitted by broker/data terms, starting when collection is enabled.

## Current next engineering phases
1. Add TLS reverse-proxy configuration, API authentication, rate limiting and WebSocket query-secret redaction before public exposure.
2. Add multi-client stream management, reconnect/backoff, bounded tick fan-out and secured browser UI integration.
3. Add snapshot persistence with timestamped archive.
4. Add paper-trading execution, fill simulation and risk controls.
5. Validate disconnect/reconnect and order reconciliation before considering any live order capability.
