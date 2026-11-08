# NSE Algo Terminal — Professional UI Preview

A standalone workspace for an NSE F&O multi-strategy options terminal, with Zerodha Kite Connect integration planned for later phases.

## Current build: frontend preview
- Professional dark trading-terminal layout with responsive mobile navigation
- Overview dashboard and system-health panel
- Universal option-chain workspace for index and stock F&O, with expiry selectors, exact strike builder, CE/PE layout, and Live / Historical Replay controls
- Market scanner workspace for volume, OI, premium, IV and PCR signals
- Multi-strategy manager and multi-leg strategy draft builder
- Per-strategy entry sequencing, stop-loss action and rejected/unfilled-leg policy
- Per-leg quantity, order type, stop loss and target fields
- Separate Paper, Live (locked), order-history and portfolio-risk workspaces
- Global risk policy configuration preview and live-readiness checklist

## Important status
This is a frontend preview only. No live NSE market feed, current contract master, Kite Connect authentication, backend, persistent database, historical data connector, paper execution simulator, risk enforcement, or real order execution is connected. The historical replay controls are UI-only until the backend connector is built. Any figures or preset strategies shown are illustrative and must not be treated as market data or trading signals.

## Planned engineering phases
1. Backend service, database, authentication, secure secrets management and audit logging.
2. Current NSE instrument master and Kite Connect market-data/WebSocket integration.
3. Historical candle service and (separately) archived/licensed historical option-chain snapshots for replay; then paper execution simulator with slippage, order types, partial fills and rejection handling.
4. Independent multi-leg strategy engines with deterministic order-state tracking and reconciliation.
5. Server-side portfolio risk manager: daily loss, exposure, capital allocation, duplicate-order protection, disconnect safeguards and emergency controls.
6. Broker live execution only after current broker/exchange requirements are verified, deployment controls are in place, and end-to-end paper tests pass.

## Security
Never commit API keys, API secrets, access tokens, PINs, TOTP seeds or other broker credentials to this repository or frontend code. Credentials must remain server-side in a secure secret store.


## Required study mode: market-closed option chain
The Option Chain must remain useful after NSE market hours. When the market is closed, show the latest available contract prices/previous-session close for every available strike in the selected underlying and expiry, clearly labelled **MARKET CLOSED** with the exchange date and last-traded timestamp where available. Keep CE and PE side-by-side and retain OI, change in OI and session volume only when returned by the API; distinguish stale/unavailable bid-ask quotes from live quotes. Do not imply that closed-session values are executable live prices.

For reliable study history, the backend should save an end-of-session option-chain snapshot for all selected active F&O contracts (instrument token, symbol, expiry, strike, CE/PE, LTP/close, OHLC, volume, OI, quote timestamp and available depth fields). This archive starts from the date integration is enabled. Kite historical candles alone do not recreate a complete historical chain for past dates or expired strikes, so older chain history must not be fabricated.
