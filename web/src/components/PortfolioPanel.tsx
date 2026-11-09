import {
  Bitcoin,
  CircleDollarSign,
  Coins,
  Eye,
  EyeOff,
  RefreshCw,
} from "lucide-react";
import type { Balance, Wallet } from "../types";
import { balanceTotal, money, quantityFormat } from "../utils";

type Props = {
  walletName: string | undefined;
  wallets: Wallet[];
  walletId: string;
  balances: Balance[];
  balancesLoading: boolean;
  showBalances: boolean;
  totalPortfolioUsd: number;
  usdPrices: Record<string, number | null>;
  unpricedAssets: string[];
  pricesError: string;
  hasWallet: boolean;
  onToggleBalances: () => void;
  onRefresh: () => void;
};

function assetName(asset: string) {
  switch (asset) {
    case "USD":
      return "US Dollar";
    case "USDT":
      return "Tether";
    case "BTC":
      return "Bitcoin";
    case "ETH":
      return "Ethereum";
    default:
      return asset;
  }
}

function AssetIcon({ asset }: { asset: string }) {
  if (asset === "BTC") return <Bitcoin size={17} />;
  if (asset === "ETH") return <Coins size={16} />;
  return <CircleDollarSign size={16} />;
}

export default function PortfolioPanel({
  walletName,
  wallets,
  walletId,
  balances,
  balancesLoading,
  showBalances,
  totalPortfolioUsd,
  usdPrices,
  unpricedAssets,
  pricesError,
  hasWallet,
  onToggleBalances,
  onRefresh,
}: Props) {
  const hasUnpricedAssets = unpricedAssets.length > 0;

  return (
    <article className="panel portfolio-panel">
      <div className="panel-heading mb-5 flex items-center justify-between gap-4">
        <div>
          <span className="eyebrow">PORTFOLIO</span>
          <h2>Total wallet value</h2>
        </div>
        <button
          className="icon-button subtle-button"
          aria-label={showBalances ? "Hide balances" : "Show balances"}
          onClick={onToggleBalances}
        >
          {showBalances ? <Eye size={17} /> : <EyeOff size={17} />}
        </button>
      </div>

      <div className="portfolio-total">
        {showBalances ? money(totalPortfolioUsd, "USD", 2) : "••••••••"}
      </div>

      <div className="portfolio-subtitle">
        <span className="portfolio-dot" />
        {walletName ||
          wallets.find((item) => String(item.id) === walletId)?.name ||
          "Selected wallet"}
        <span className="subtle-separator">·</span>
        {hasUnpricedAssets ? "Partial valuation" : "Estimated value"}
      </div>

      {showBalances && hasUnpricedAssets && (
        <div
          className="error-banner"
          role="status"
          style={{ marginTop: "12px", marginBottom: "12px" }}
        >
          <span>
            Market price unavailable for{" "}
            <strong>{unpricedAssets.join(", ")}</strong>. The total above
            includes only assets with known prices and is not the complete
            wallet value.
          </span>
        </div>
      )}

      {showBalances && !hasUnpricedAssets && pricesError && (
        <div
          className="error-banner"
          role="status"
          style={{ marginTop: "12px", marginBottom: "12px" }}
        >
          Market prices could not be refreshed. The displayed valuation may use
          previously loaded prices.
        </div>
      )}

      <div className="portfolio-divider" />
      <div className="balance-table-heading">
        <span>ASSET</span>
        <span>AVAILABLE</span>
        <span>TOTAL VALUE</span>
      </div>

      {balancesLoading && balances.length === 0 ? (
        <div className="loading-row">
          <RefreshCw size={16} className="spin" />
          Loading balances…
        </div>
      ) : balances.length === 0 ? (
        <div className="empty-inline">No balances available for this wallet yet.</div>
      ) : (
        <div className="balance-list">
          {balances.map((balance) => {
            const amount = balanceTotal(balance);
            const price = usdPrices[balance.asset];
            const isUnpriced =
              amount !== 0 && (price === null || price === undefined);
            const usdValue =
              price !== null && price !== undefined ? amount * price : null;

            return (
              <div className="balance-row" key={balance.asset}>
                <div className="balance-asset">
                  <span
                    className={`balance-coin balance-coin-${balance.asset.toLowerCase()}`}
                  >
                    <AssetIcon asset={balance.asset} />
                  </span>
                  <span>
                    <strong>{balance.asset}</strong>
                    <small>{assetName(balance.asset)}</small>
                  </span>
                </div>

                <div className="balance-available">
                  <span>
                    {showBalances ? quantityFormat(balance.available) : "••••"}
                  </span>
                  <small
                    style={{
                      display: "block",
                      opacity: 0.65,
                      fontSize: "11px",
                      marginTop: "3px",
                    }}
                  >
                    Reserved:{" "}
                    {showBalances
                      ? quantityFormat(balance.reserved || "0")
                      : "••••"}
                  </small>
                </div>

                <div className="balance-value">
                  {!showBalances
                    ? "••••"
                    : isUnpriced
                      ? "Price unavailable"
                      : money(usdValue ?? 0, "USD", 2)}
                </div>
              </div>
            );
          })}
        </div>
      )}

      <button
        className="secondary-button full-width-button"
        onClick={onRefresh}
        disabled={balancesLoading || !hasWallet}
      >
        <RefreshCw
          size={15}
          className={balancesLoading ? "spin" : ""}
        />
        Refresh balances
      </button>
    </article>
  );
}
