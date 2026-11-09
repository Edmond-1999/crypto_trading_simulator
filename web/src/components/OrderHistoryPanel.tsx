import type { Order } from "../types";
import { orderQuoteCurrency, money, quantityFormat, shortDate } from "../utils";
import {
  ArrowDownLeft,
  ArrowUpRight,
  Clock3,
  RefreshCw,
} from "lucide-react";

type Props = {
  title: "Recent activity" | "Order history";
  orders: Order[];
  loading: boolean;
  error: string;
  hasWallet: boolean;
  showAllOrders: boolean;
  onRefresh: () => void;
};

export default function OrderHistoryPanel({
  title,
  orders,
  loading,
  error,
  hasWallet,
  showAllOrders,
  onRefresh,
}: Props) {
  const visibleOrders = showAllOrders ? orders : orders.slice(0, 5);

  return (
    <section className="panel activity-panel">
      <div className="panel-heading mb-5 flex items-center justify-between gap-4">
        <div>
          <span className="eyebrow">SIMULATED ORDERS</span>
          <h2>{title}</h2>
        </div>
        <button
          className="text-button"
          type="button"
          onClick={onRefresh}
          disabled={loading || !hasWallet}
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
      {loading && orders.length === 0 ? (
        <div className="loading-row">
          <RefreshCw size={16} className="spin" />
          Loading orders…
        </div>
      ) : orders.length === 0 ? (
        <div className="empty-activity">
          <span className="empty-icon">
            <Clock3 size={20} />
          </span>
          <strong>No simulated orders yet</strong>
          <p>Completed spot trades will appear here.</p>
        </div>
      ) : (
        <div className="order-table-wrap">
          <div className="order-table-head">
            <span>ORDER</span>
            <span>QUANTITY</span>
            <span>PRICE</span>
            <span>QUOTE AMOUNT</span>
            <span>FEE</span>
            <span>STATUS</span>
            <span>DATE</span>
          </div>
          {visibleOrders.map((order) => {
            const isBuy = order.side.toUpperCase() === "BUY";
            const SideIcon = isBuy ? ArrowDownLeft : ArrowUpRight;
            const quoteCurrency = orderQuoteCurrency(order);

            return (
              <div className="order-table-row" key={order.id}>
                <div className="order-cell order-title-cell">
                  <span
                    className={`order-side-icon ${isBuy ? "order-buy" : "order-sell"}`}
                  >
                    <SideIcon size={16} />
                  </span>
                  <span>
                    <strong>
                      {order.side.toUpperCase()}{" "}
                      {order.base_asset ||
                        (order.base_asset_id
                          ? `Asset #${order.base_asset_id}`
                          : "spot")}
                    </strong>
                    <small>Order #{order.id}</small>
                  </span>
                </div>
                <span className="order-cell">
                  {quantityFormat(order.quantity)}
                </span>
                <span className="order-cell">
                  {money(order.price, quoteCurrency, 4)}
                </span>
                <span className="order-cell">
                  {money(order.quote_amount, quoteCurrency, 4)}
                </span>
                <span className="order-cell">
                  {money(order.fee_amount || order.fee || "0", quoteCurrency, 4)}
                </span>
                <span
                  className={`order-status ${order.status.toLowerCase() === "filled" ? "order-status-filled" : ""}`}
                >
                  {order.status}
                </span>
                <span className="order-cell">{shortDate(order.created_at)}</span>
              </div>
            );
          })}
        </div>
      )}
    </section>
  );
}
