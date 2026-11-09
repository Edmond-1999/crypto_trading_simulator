# NexaTrade — Cryptocurrency Trading Simulator

A full-stack cryptocurrency trading simulation platform featuring real-time market data, spot market trading, accurate cost-basis accounting, portfolio profit/loss (P&L) tracking, and TradingView candlestick charting.

---

## Architecture & Tech Stack

* **Backend**: Python 3.12+ / 3.14, Flask, SQLAlchemy, Alembic (database migrations), Flask-JWT-Extended, Pytest.
* **Database**: PostgreSQL (production/local dev) / SQLite (in-memory test suite).
* **Frontend**: React 19, TypeScript, Vite, Tailwind CSS, TradingView Lightweight Charts, Lucide Icons.
* **Market Data**: Binance API (real-time ticker and candlestick data) + Coinbase API (USDT/USD reference rates).

---

## Key Features

1. **User Authentication & Wallet Management**:
   - Secure JWT-based registration, login, and token refresh.
   - Multi-wallet support denominated in USD or USDT base currencies.
2. **Simulated Spot Market Trading**:
   - Market BUY and SELL orders with realistic 0.1% fee calculation.
   - Double-entry balance reservations and ledger entry tracking.
   - Atomic balance updates with database row locking (`SELECT FOR UPDATE`).
3. **Accurate Cost-Basis & P&L Accounting**:
   - Distinguishes known-cost purchases from unknown-cost historical holdings or deposits.
   - Avoids fabricating unrealized gains/losses for assets with unknown acquisition cost.
4. **Interactive Market Charts & Tickers**:
   - Real-time candlestick charts with multiple intervals (`1m`, `5m`, `15m`, `1h`, `4h`, `1d`).
   - Live price indicators for BTC and ETH in USD and USDT.
5. **Demo Funding Faucet**:
   - Deposit simulated USD, USDT, BTC, or ETH directly into demo wallets.

---

## Directory Structure

```text
crypto_trading_simulator/
├── backend/                  # Flask REST API
│   ├── app/
│   │   ├── models/           # SQLAlchemy models (User, Wallet, Asset, Balance, TradeOrder, etc.)
│   │   ├── routes/           # Blueprint routes (auth, wallets, balances, orders, market, pnl, deposits)
│   │   ├── services/         # Business logic (trading, pnl, market prices, deposits)
│   │   └── config.py         # App configuration & environment loader
│   ├── migrations/           # Alembic database migrations
│   ├── tests/                # Automated pytest test suite
│   ├── requirements.txt      # Python dependencies
│   └── .env.example          # Backend environment template
├── web/                      # React + Vite frontend
│   ├── src/
│   │   ├── components/       # UI components (TradingChart, TradePanel, PnlPanel, etc.)
│   │   ├── App.tsx           # Main application state and view routing
│   │   └── types.ts          # TypeScript type definitions
│   └── package.json          # Node dependencies and scripts
├── docker-compose.yml        # PostgreSQL container service
├── .gitignore                # Git ignore rules
└── README.md                 # Project documentation
```

---

## Getting Started

### 1. Prerequisites
* **Python 3.12+**
* **Node.js 18+** & **npm**
* **Docker** (optional, for local PostgreSQL)

### 2. Database Setup (PostgreSQL)
Start PostgreSQL using Docker:
```bash
docker compose up -d
```
Alternatively, use an existing local PostgreSQL instance matching the credentials in `.env.example`.

### 3. Backend Setup
Navigate to the `backend/` directory:
```bash
cd backend
python -m venv .venv

# On Windows (PowerShell):
.venv\Scripts\Activate.ps1
# On Linux / macOS:
source .venv/bin/activate

pip install -r requirements.txt
cp .env.example .env
flask db upgrade
flask run --port 5000
```

### 4. Frontend Setup
Navigate to the `web/` directory:
```bash
cd web
npm install
npm run dev
```
Open `http://localhost:5173` in your browser.

---

## Running Verification & Tests

### Backend Tests (Pytest)
```bash
cd backend
python -m pytest -v
```
All 46 unit and integration tests will execute against an in-memory SQLite database.

### Frontend Lint & Build
```bash
cd web
npm run lint
npm run build
```

---

## API Summary

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `POST` | `/api/v1/auth/register` | Register new user account |
| `POST` | `/api/v1/auth/login` | Log in and receive JWT bearer token |
| `GET` | `/api/v1/auth/me` | Fetch authenticated user profile |
| `GET` | `/api/v1/wallets` | List current user's wallets |
| `POST` | `/api/v1/wallets` | Create a new wallet |
| `GET` | `/api/v1/wallets/<id>/balances` | Retrieve asset balances |
| `POST` | `/api/v1/wallets/<id>/deposits` | Simulated demo fund deposit |
| `GET` | `/api/v1/wallets/<id>/orders` | Get trade order history |
| `POST` | `/api/v1/wallets/<id>/orders` | Execute spot market order (BUY/SELL) |
| `GET` | `/api/v1/wallets/<id>/pnl` | Fetch position cost basis and realized/unrealized P&L |
| `GET` | `/api/v1/market/prices` | Live indicative market prices (BTC, ETH) |
