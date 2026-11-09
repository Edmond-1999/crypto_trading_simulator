import {
  Bitcoin,
  CircleDollarSign,
  Coins,
  RefreshCw,
} from "lucide-react";
import TradingChart from "../TradingChart.tsx";
import type { MarketPrices, NavigationSection } from "../types";
import { money, positivePrice } from "../utils";

type Props = {
  activeSection: NavigationSection;
  prices: MarketPrices;
  pricesLoading: boolean;
  pricesError: string;
  usdtUsdRate: number | null;
  onRefresh: () => void;
};

const marketAssets = [
  {
    symbol: "BTC",
    name: "Bitcoin",
    icon: Bitcoin,
    iconClass: "bitcoin-icon",
    cardClass: "",
  },
  {
    symbol: "ETH",
    name: "Ethereum",
    icon: Coins,
    iconClass: "ethereum-icon",
    cardClass: "",
  },
  {
    symbol: "USDT",
    name: "Tether",
    icon: CircleDollarSign,
    iconClass: "usdt-icon",
    cardClass: "stablecoin-card",
  },
];

export default function MarketSection({
  activeSection,
  prices,
  pricesLoading,
  pricesError,
  usdtUsdRate,
  onRefresh,
}: Props) {
  const showMarkets =
    activeSection === "Dashboard" || activeSection === "Markets";

  if (!showMarkets) return null;

  return (
    <>
      <section className="market-section" id="markets-panel">
        <div className="section-heading mb-[18px] flex items-center justify-between gap-4 max-[620px]:items-start">
          <div>
            <span className="eyebrow">MARKET OVERVIEW</span>
            <h2>Markets at a glance</h2>
          </div>
          <button
            className="text-button"
            onClick={onRefresh}
            disabled={pricesLoading}
          >
            <RefreshCw
              size={14}
              className={pricesLoading ? "spin" : ""}
            />
            Refresh prices
          </button>
        </div>

        {pricesError && (
          <div className="error-banner" role="alert">
            {pricesError}
          </div>
        )}

        <div className="market-grid grid grid-cols-3 gap-[15px] max-[900px]:gap-[10px] max-[620px]:grid-cols-1">
          {marketAssets.map(({ symbol, name, icon: Icon, iconClass, cardClass }) => {
            const value =
              symbol === "USDT"
                ? usdtUsdRate
                : positivePrice(prices.prices?.[symbol]?.USD);

            return (
              <article
                className={`market-card ${cardClass}`}
                key={symbol}
              >
                <div className="market-card-top">
                  <span className={`coin-icon ${iconClass}`}>
                    <Icon size={symbol === "BTC" ? 22 : 21} />
                  </span>
                  <div className="market-name">
                    <strong>{name}</strong>
                    <span>{symbol} / USD</span>
                  </div>
                  <span className="market-symbol">{symbol}</span>
                </div>
                <div className="market-price">
                  {value === null
                    ? "—"
                    : money(value, "USD", symbol === "USDT" ? 4 : 2)}
                </div>
                <div className="market-card-bottom">
                  <span className="market-source">
                    {symbol === "USDT"
                      ? "Indicative conversion rate"
                      : "Indicative market price"}
                  </span>
                  <span className="market-live-dot" />
                </div>
              </article>
            );
          })}
        </div>

        <p className="data-caption">
          {prices.source || "Market data"} · Prices refresh automatically every
          30 seconds. Execution prices may differ.
        </p>
      </section>

      <section className="chart-section" id="chart-panel">
        <TradingChart />
      </section>
    </>
  );
}
