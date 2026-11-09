import type { FormEvent } from "react";
import { ChevronDown, RefreshCw, X } from "lucide-react";
import type { QuoteCurrency } from "../types";

type Props = {
  open: boolean;
  name: string;
  currency: QuoteCurrency;
  creating: boolean;
  onNameChange: (name: string) => void;
  onCurrencyChange: (currency: QuoteCurrency) => void;
  onClose: () => void;
  onSubmit: (event: FormEvent<HTMLFormElement>) => void;
};

export default function WalletModal({
  open,
  name,
  currency,
  creating,
  onNameChange,
  onCurrencyChange,
  onClose,
  onSubmit,
}: Props) {
  if (!open) return null;

  return (
    <div
      className="modal-backdrop"
      onClick={(event) => {
        if (event.target === event.currentTarget) onClose();
      }}
    >
      <section
        className="modal-card"
        role="dialog"
        aria-modal="true"
        aria-labelledby="wallet-modal-title"
      >
        <div className="modal-heading">
          <div>
            <span className="eyebrow">NEW SIMULATOR WALLET</span>
            <h2 id="wallet-modal-title">Create wallet</h2>
          </div>
          <button
            className="icon-button"
            type="button"
            aria-label="Close dialog"
            onClick={onClose}
          >
            <X size={17} />
          </button>
        </div>
        <p className="modal-description">
          Create a separate demo wallet for simulated spot trades.
        </p>
        <form className="wallet-setup" onSubmit={onSubmit}>
          <label className="field-label" htmlFor="wallet-name">
            Wallet name
          </label>
          <input
            id="wallet-name"
            className="form-input"
            type="text"
            maxLength={100}
            value={name}
            onChange={(event) => onNameChange(event.target.value)}
            required
          />
          <label className="field-label" htmlFor="wallet-currency">
            Base currency
          </label>
          <div className="select-wrap">
            <select
              id="wallet-currency"
              className="form-input"
              value={currency}
              onChange={(event) =>
                onCurrencyChange(event.target.value as QuoteCurrency)
              }
            >
              <option value="USD">US Dollar (USD)</option>
              <option value="USDT">Tether (USDT)</option>
            </select>
            <ChevronDown size={15} />
          </div>
          <div className="modal-actions">
            <button
              className="secondary-button"
              type="button"
              onClick={onClose}
              disabled={creating}
            >
              Cancel
            </button>
            <button
              className="primary-button"
              type="submit"
              disabled={creating || !name.trim()}
            >
              {creating && <RefreshCw size={15} className="spin" />}
              {creating ? "Creating…" : "Create wallet"}
            </button>
          </div>
        </form>
      </section>
    </div>
  );
}
