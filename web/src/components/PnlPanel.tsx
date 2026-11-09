import { RefreshCw } from "lucide-react";
import type { WalletPnl } from "../types";
import { money, quantityFormat } from "../utils";

type Props = {
  pnl: WalletPnl | null;
  loading: boolean;
  error: string;
  onRefresh: () => void;
};

export default function PnlPanel({ pnl, loading, error, onRefresh }: Props) {
  return (
    <article className="panel">
      <div className="panel-heading mb-5 flex items-center justify-between gap-4">
        <div>
          <span className="eyebrow">PERFORMANCE</span>
          <h2>Wallet profit &amp; loss</h2>
        </div>
        <button
          className="text-button"
          type="button"
          onClick={onRefresh}
          disabled={loading}
        >
          <RefreshCw size={14} className={loading ? "spin" : ""} />
          Refresh
        </button>
      </div>

      {error && (
        <div className="error-banner" role="alert">
          {error}
        </div>
      )}

      {loading && !pnl ? (
        <div className="loading-row">
          <RefreshCw size={16} className="spin" />
          Loading P&amp;L…
        </div>
      ) : pnl ? (
        <>
          <div className="pnl-total">
            {pnl.total_pnl_usd === null
              ? "Incomplete"
              : money(pnl.total_pnl_usd, "USD", 2)}
          </div>
          <div className="pnl-metrics">
            <div>
              <span>Realized P&amp;L</span>
              <strong>
                {money(pnl.realized_pnl_usd, "USD", 2)}
                {!pnl.realized_pnl_complete && " · Partial"}
              </strong>
            </div>
            <div>
              <span>Unrealized P&amp;L</span>
              <strong>
                {pnl.unrealized_pnl_usd === null
                  ? "Unavailable"
                  : money(pnl.unrealized_pnl_usd, "USD", 2)}
                {!pnl.unrealized_pnl_complete && " · Partial"}
              </strong>
            </div>
          </div>
          {pnl.positions.length > 0 ? (
            <div className="pnl-position-list">
              {pnl.positions.map((position) => (
                <div className="pnl-position-row" key={position.asset}>
                  <span>
                    <strong>{position.asset}</strong>
                    <small>
                      {quantityFormat(
                        position.total_quantity ??
                          String(
                            Number(position.known_quantity) +
                              Number(position.unknown_quantity),
                          ),
                      )}{" "}
                      units
                    </small>
                  </span>
                  <span>
                    <strong>
                      {position.market_value_usd === null ||
                      position.market_value_usd === undefined
                        ? "Value unavailable"
                        : money(position.market_value_usd, "USD", 2)}
                    </strong>
                    <small>
                      {position.unrealized_pnl_usd === null
                        ? "P&L unavailable"
                        : `${money(position.unrealized_pnl_usd, "USD", 2)}${position.unrealized_pnl_complete ? "" : " · Partial"}`}
                    </small>
                  </span>
                </div>
              ))}
            </div>
          ) : (
            <div className="empty-inline">No open positions to report.</div>
          )}
          {pnl.notes?.length ? (
            <p className="pnl-warning">{pnl.notes[0]}</p>
          ) : null}
        </>
      ) : (
        <div className="empty-inline">P&amp;L is not available yet.</div>
      )}
    </article>
  );
}
