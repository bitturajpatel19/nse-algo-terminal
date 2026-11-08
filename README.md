# NSE Algo Terminal — Phase 1 Prototype

A separate project for an NSE F&O multi-strategy terminal integrated with Zerodha Kite Connect in later phases.

## Phase 1
- Responsive dashboard UI
- Paper / Live mode selector (Live is deliberately locked)
- Multi-strategy manager with pause/resume
- Multi-leg strategy builder
- Per-leg stop loss fields and strategy-level max loss/target
- Per-strategy entry sequencing and stop-loss action choices
- Rejected/unfilled leg handling choices
- Demo scanner and order/leg monitor layouts

## Not connected yet
- No NSE live market feed or current F&O contract master
- No Zerodha/Kite Connect authentication
- No WebSocket stream
- No real order placement, modification, or cancellation
- No persistent server-side strategy/order database
- No live risk enforcement

## Roadmap
1. Backend service, database, authentication, and secrets management.
2. NSE instrument master and Kite Connect market data/WebSocket integration.
3. Paper execution simulator with partial-fill and slippage handling.
4. Multi-leg execution state machine and order reconciliation.
5. Per-leg and strategy-level risk engine, kill switch, and audit log.
6. Live integration only after broker/exchange compliance checks, deployment requirements, testing, and explicit user enablement.

Never commit API keys, API secrets, access tokens, PINs, or TOTP seeds to frontend files or GitHub.
