import type { FormEvent } from "react";
import { ArrowDownLeft, RefreshCw } from "lucide-react";
import type { DepositAsset } from "../types";

type Props = {
  asset: DepositAsset;
  amount: string;
  loading: boolean;
  error: string;
  hasWallet: boolean;
  onAssetChange: (asset: DepositAsset) => void;
  onAmountChange: (amount: string) => void;
  onSubmit: (event: FormEvent<HTMLFormElement>) => void;
};

export default function FundingPanel({
  asset,
  amount,
  loading,
  error,
  hasWallet,
  onAssetChange,
  onAmountChange,
  onSubmit,
}: Props) {
  return (
    <article className="panel">
      <div className="panel-heading mb-5 flex items-center justify-between gap-4">
        <div>
          <span className="eyebrow">DEMO FUNDS</span>
          <h2>Add simulated funds</h2>
        </div>
        <ArrowDownLeft size={18} />
      </div>
      <p className="modal-description">
        Add test assets to this simulator wallet. Deposits are not real and
        cannot be withdrawn or sent to an exchange.
      </p>
      <form className="trade-form funding-form" onSubmit={onSubmit}>
        <label htmlFor="deposit-asset">Asset</label>
        <select
          id="deposit-asset"
          value={asset}
          onChange={(event) => onAssetChange(event.target.value as DepositAsset)}
        >
          <option value="USD">US Dollar (USD)</option>
          <option value="USDT">Tether (USDT)</option>
          <option value="BTC">Bitcoin (BTC)</option>
          <option value="ETH">Ethereum (ETH)</option>
        </select>
        <label htmlFor="deposit-amount">Amount</label>
        <input
          id="deposit-amount"
          type="number"
          min="0"
          step="any"
          inputMode="decimal"
          value={amount}
          onChange={(event) => onAmountChange(event.target.value)}
          required
        />
        {error && (
          <div className="error-banner" role="alert">
            {error}
          </div>
        )}
        <button
          className="primary-button"
          type="submit"
          disabled={loading || !hasWallet}
        >
          {loading && <RefreshCw size={15} className="spin" />}
          {loading ? "Adding funds…" : "Add demo funds"}
        </button>
      </form>
    </article>
  );
}
