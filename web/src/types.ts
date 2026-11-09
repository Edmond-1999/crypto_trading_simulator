export type AuthMode = "login" | "register";
export type TradeSide = "BUY" | "SELL";
export type AssetSymbol = "BTC" | "ETH";
export type QuoteCurrency = "USD" | "USDT";
export type DepositAsset = QuoteCurrency | AssetSymbol;
export type NavigationSection = "Dashboard" | "Markets" | "Trade" | "Activity";

export type User = {
  id?: number;
  email: string;
};

export type MarketPrices = {
  source?: string;
  usdt_usd_rate?: string;
  prices?: Record<string, Record<string, string>>;
};

export type Balance = {
  asset: string;
  available: string;
  reserved: string;
  total: string;
};

export type Wallet = {
  id: number;
  name: string;
  base_currency: string;
};

export type WalletResponse = {
  wallet_id?: number;
  wallet_name?: string;
  base_currency?: string;
  balances?: Balance[];
};

export type PnlPosition = {
  asset: string;
  known_quantity: string;
  unknown_quantity: string;
  total_quantity?: string;
  known_cost_basis_usd: string;
  market_price_usd: string | null;
  known_market_value_usd?: string | null;
  unknown_market_value_usd?: string | null;
  market_value_usd?: string | null;
  unrealized_pnl_usd: string | null;
  unrealized_pnl_complete: boolean;
};

export type WalletPnl = {
  wallet_id: number;
  currency: string;
  realized_pnl_usd: string;
  realized_pnl_complete: boolean;
  unrealized_pnl_usd: string | null;
  unrealized_pnl_complete: boolean;
  total_pnl_usd: string | null;
  positions: PnlPosition[];
  notes?: string[];
};

export type Order = {
  id: number;
  wallet_id?: number;
  side: string;
  type?: string;
  order_type?: string;
  quantity: string;
  price: string;
  quote_amount: string;
  fee_amount?: string;
  fee?: string;
  fee_rate?: string;
  price_source?: string;
  status: string;
  created_at: string;
  base_asset_id?: number;
  quote_asset_id?: number;
  base_asset?: string;
  quote_currency?: string;
};
