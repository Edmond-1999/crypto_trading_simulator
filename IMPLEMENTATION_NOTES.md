# Crypto Currency Trading Simulator — implementation update

## Included in this update

- Wallet P&L now looks up an indicative market price for any held BTC/ETH position, including holdings whose acquisition cost is unknown.
- P&L position rows distinguish total market value from known-cost market value and keep unknown-cost holdings out of invented profit/loss calculations.
- Simulated BTC/ETH deposits are recorded as unknown-cost units in the position cost-basis ledger.
- P&L reporting has a balance fallback for BTC/ETH holdings that do not yet have a cost-basis record.
- The frontend now loads wallet P&L, shows position market values and P&L completeness, and provides a simulated-funding form.
- Sidebar navigation now switches between Dashboard, Markets, Spot trading, and Order history views.
- Added API tests for P&L access controls, unknown-cost valuation, and crypto-deposit cost-basis tracking.
- Converted `backend/requirements.txt` from UTF-16 to UTF-8 for better portability.

## Safety and accounting notes

- This remains a **simulator**. Orders and deposits do not execute on an exchange or move real funds.
- Market prices are indicative and may be unavailable or change between quote and simulated order.
- Holdings with unknown acquisition cost can have an estimated market value, but must not be presented as having a known unrealized profit/loss.
- Do not send wallet private keys or recovery phrases to the backend.

## Verification

Run backend tests from `backend/` with `python -m pytest -v`. Run frontend checks from `web/` with `npm ci`, `npm run lint`, and `npm run build`.