import type { FormEvent } from "react";
import {
  ArrowDownLeft,
  ArrowUpRight,
  ChevronDown,
  RefreshCw,
  ShieldCheck,
} from "lucide-react";
import type {
  AssetSymbol,
  QuoteCurrency,
  TradeSide,
  WalletResponse,
} from "../types";
import { money, quantityFormat } from "../utils";

type Props = {
  hasWallet: boolean;
  wallet: WalletResponse | null;
  balancesLoading: boolean;
  side: TradeSide;
  selectedAsset: AssetSymbol;
  quoteCurrency: QuoteCurrency;
  quantity: string;
  selectedPrice: number;
  estimatedTotal: number;
  estimatedFee: number;
  estimatedDebit: number;
  availableQuoteBalance: number;
  availableBaseBalance: number;
  insufficientBalance: boolean;
  validQuantity: boolean;
  submittingOrder: boolean;
  orderError: string;
  onSideChange: (side: TradeSide) => void;
  onAssetChange: (asset: AssetSymbol) => void;
  onQuoteCurrencyChange: (currency: QuoteCurrency) => void;
  onQuantityChange: (quantity: string) => void;
  onSubmit: (event: FormEvent<HTMLFormElement>) => void;
};

export default function TradePanel({
  hasWallet,
  wallet,
  balancesLoading,
  side,
  selectedAsset,
  quoteCurrency,
  quantity,
  selectedPrice,
  estimatedTotal,
  estimatedFee,
  estimatedDebit,
  availableQuoteBalance,
  availableBaseBalance,
  insufficientBalance,
  validQuantity,
  submittingOrder,
  orderError,
  onSideChange,
  onAssetChange,
  onQuoteCurrencyChange,
  onQuantityChange,
  onSubmit,
}: Props) {
  return (
    <article className="panel trade-panel" id="trade-panel">
      <div className="panel-heading mb-5 flex items-center justify-between gap-4">
        <div>
          <span className="eyebrow">SPOT MARKET</span>
          <h2>Quick trade</h2>
        </div>
        <span className="demo-badge">
          <span className="online-dot" />
          SIMULATED
        </span>
      </div>

      <div className="trade-tabs" role="group" aria-label="Trade side">
        <button
          className={`trade-tab buy-tab ${side === "BUY" ? "active" : ""}`}
          type="button"
          aria-pressed={side === "BUY"}
          onClick={() => onSideChange("BUY")}
        >
          <ArrowDownLeft size={15} />
          Buy
        </button>
        <button
          className={`trade-tab sell-tab ${side === "SELL" ? "active" : ""}`}
          type="button"
          aria-pressed={side === "SELL"}
          onClick={() => onSideChange("SELL")}
        >
          <ArrowUpRight size={15} />
          Sell
        </button>
      </div>

      <form className="trade-form" onSubmit={onSubmit}>
        <label className="field-label" htmlFor="trade-asset">
          Asset
        </label>
        <div className="select-wrap">
          <select
            id="trade-asset"
            className="form-input"
            value={selectedAsset}
            onChange={(event) => onAssetChange(event.target.value as AssetSymbol)}
          >
            <option value="BTC">Bitcoin (BTC)</option>
            <option value="ETH">Ethereum (ETH)</option>
          </select>
          <ChevronDown size={15} />
        </div>

        <label className="field-label" htmlFor="trade-quote">
          Quote currency
        </label>
        <div className="select-wrap">
          <select
            id="trade-quote"
            className="form-input"
            value={quoteCurrency}
            onChange={(event) =>
              onQuoteCurrencyChange(event.target.value as QuoteCurrency)
            }
          >
            <option value="USD">US Dollar (USD)</option>
            <option value="USDT">Tether (USDT)</option>
          </select>
          <ChevronDown size={15} />
        </div>

        <div className="field-row-heading">
          <label className="field-label" htmlFor="trade-quantity">
            Quantity
          </label>
          <span className="field-hint">{selectedAsset}</span>
        </div>
        <input
          id="trade-quantity"
          className="form-input quantity-input"
          type="number"
          min="0"
          step="any"
          inputMode="decimal"
          value={quantity}
          onChange={(event) => onQuantityChange(event.target.value)}
          required
        />

        <div className="available-row">
          <span>Available to {side.toLowerCase()}</span>
          <strong>
            {side === "BUY"
              ? `${quantityFormat(availableQuoteBalance)} ${quoteCurrency}`
              : `${quantityFormat(availableBaseBalance)} ${selectedAsset}`}
          </strong>
        </div>

        {side === "BUY" && insufficientBalance && validQuantity && (
          <div className="error-banner" role="status">
            Not enough {quoteCurrency} available for this order and fee.
          </div>
        )}
        {side === "SELL" && insufficientBalance && validQuantity && (
          <div className="error-banner" role="status">
            Not enough {selectedAsset} available for this order.
          </div>
        )}
        {orderError && (
          <div className="error-banner" role="alert">
            {orderError}
          </div>
        )}

        <div className="trade-estimate">
          <div className="estimate-row">
            <span>Indicative price</span>
            <strong>
              {selectedPrice > 0
                ? money(selectedPrice, quoteCurrency, 4)
                : "Price unavailable"}
            </strong>
          </div>
          <div className="estimate-row">
            <span>Estimated order value</span>
            <strong>{money(estimatedTotal, quoteCurrency, 4)}</strong>
          </div>
          <div className="estimate-row">
            <span>Estimated fee (0.1%)</span>
            <strong>{money(estimatedFee, quoteCurrency, 4)}</strong>
          </div>
          <div className="estimate-row estimate-total">
            <span>
              {side === "BUY" ? "Estimated debit" : "Estimated proceeds"}
            </span>
            <strong>
              {money(
                side === "BUY" ? estimatedDebit : estimatedTotal - estimatedFee,
                quoteCurrency,
                4,
              )}
            </strong>
          </div>
        </div>

        <button
          className={`primary-button trade-submit ${side === "SELL" ? "sell-submit" : ""}`}
          type="submit"
          disabled={
            !hasWallet ||
            !wallet ||
            balancesLoading ||
            submittingOrder ||
            !validQuantity ||
            selectedPrice <= 0 ||
            insufficientBalance
          }
        >
          {submittingOrder && <RefreshCw size={15} className="spin" />}
          {submittingOrder
            ? "Submitting…"
            : `${side === "BUY" ? "Buy" : "Sell"} ${selectedAsset}`}
        </button>
        <p className="trade-disclaimer">
          <ShieldCheck size={13} />
          Simulated spot trading only. Prices are indicative and no real funds
          are transferred.
        </p>
      </form>
    </article>
  );
}
