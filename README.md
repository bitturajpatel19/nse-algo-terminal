# NSE Algo Terminal — Professional UI Preview

A standalone workspace for an NSE F&O multi-strategy options terminal, with Zerodha Kite Connect integration planned for later phases.

## Current build: frontend preview
- Professional dark trading-terminal layout with responsive mobile navigation
- Overview dashboard and system-health panel
- Universal option-chain workspace for index and stock F&O, with expiry selectors and CE/PE layout
- Market scanner workspace for volume, OI, premium, IV and PCR signals
- Multi-strategy manager and multi-leg strategy draft builder
- Per-strategy entry sequencing, stop-loss action and rejected/unfilled-leg policy
- Per-leg quantity, order type, stop loss and target fields
- Separate Paper, Live (locked), order-history and portfolio-risk workspaces
- Global risk policy configuration preview and live-readiness checklist

## Important status
This is a frontend preview only. No live NSE market feed, current contract master, Kite Connect authentication, backend, persistent database, paper execution simulator, risk enforcement, or real order execution is connected. Any figures or preset strategies shown are illustrative and must not be treated as market data or trading signals.

## Planned engineering phases
1. Backend service, database, authentication, secure secrets management and audit logging.
2. Current NSE instrument master and Kite Connect market-data/WebSocket integration.
3. Paper execution simulator with slippage, order types, partial fills and rejection handling.
4. Independent multi-leg strategy engines with deterministic order-state tracking and reconciliation.
5. Server-side portfolio risk manager: daily loss, exposure, capital allocation, duplicate-order protection, disconnect safeguards and emergency controls.
6. Broker live execution only after current broker/exchange requirements are verified, deployment controls are in place, and end-to-end paper tests pass.

## Security
Never commit API keys, API secrets, access tokens, PINs, TOTP seeds or other broker credentials to this repository or frontend code. Credentials must remain server-side in a secure secret store.
