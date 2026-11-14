# NSE Algo Terminal

A responsive NSE F&O options workspace with a developing Zerodha Kite Connect backend.

## Current implementation status
- Responsive dark trading-terminal frontend preview.
- FastAPI backend with Kite login/callback and server-side access-token handling.
- Read-only option-chain quote snapshot for NIFTY, BANKNIFTY, FINNIFTY and MIDCPNIFTY.
- NFO instrument-master download/cache and health/readiness endpoints.
- Automated backend test suite and GitHub Actions workflow.
- Dockerfile and Docker Compose foundation for a future cloud VPS deployment.
- Live order placement remains disabled and is not implemented.

## Current limitations
- The frontend is still a preview; it is not yet connected to a production live market feed.
- Option-chain endpoint currently returns quote snapshots, not a continuous WebSocket stream.
- Current option-chain support is limited to the four index underlyings listed above; F&O stock contracts are not yet implemented in this endpoint.
- Kite access token is held in process memory. The backend is intentionally configured for one worker; restart requires a new login.
- No database-backed historical option-chain archive, paper execution engine, or live order execution is implemented.
- Figures shown in preview UI are illustrative, not live trading signals.

## Cloud VPS readiness
Deployment files and a step-by-step preparation guide are in `backend/`. They do not mean a VPS has been purchased, configured, or deployed. Before public deployment, we still need a provider with a fixed static public IP, a domain and HTTPS reverse proxy, API access protection/rate limiting, secure secret configuration, and registration of the originating static IP in the Kite Developer Console.

See [backend deployment guide](backend/README.md).

## Planned engineering phases
1. Complete secure public deployment controls (TLS reverse proxy, API authentication, rate limiting and monitoring).
2. Add Kite WebSocket tick streaming and a secured browser feed.
3. Add timestamped option-chain snapshot storage for future replay. Historical candles alone cannot reconstruct old full option chains or expired strikes.
4. Build paper-trading simulation, order-state tracking and portfolio risk controls.
5. Consider live execution only after current Zerodha/NSE/SEBI requirements are confirmed and end-to-end safeguards are tested.

## Security
Never commit API keys, API secrets, access tokens, PINs, TOTP seeds or other broker credentials to this repository or frontend code. Keep credentials only in a private server-side secret manager or protected environment file.
