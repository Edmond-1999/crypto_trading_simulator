import { useEffect, useRef, useState } from "react";
import {
  CandlestickSeries,
  ColorType,
  createChart,
  type CandlestickData,
  type ISeriesApi,
  type Time,
  type UTCTimestamp,
} from "lightweight-charts";
import "./TradingChart.css";

type TradingSymbol = "BTCUSDT" | "ETHUSDT";
type CandleInterval = "1m" | "5m" | "15m" | "1h" | "4h" | "1d";

interface BinanceCandle {
  time: UTCTimestamp;
  open: number;
  high: number;
  low: number;
  close: number;
}

const SYMBOLS: { label: string; value: TradingSymbol }[] = [
  { label: "BTC / USDT", value: "BTCUSDT" },
  { label: "ETH / USDT", value: "ETHUSDT" },
];

const INTERVALS: CandleInterval[] = [
  "1m",
  "5m",
  "15m",
  "1h",
  "4h",
  "1d",
];

function formatPrice(price: number): string {
  return new Intl.NumberFormat("en-US", {
    minimumFractionDigits: 2,
    maximumFractionDigits: price < 1 ? 6 : 2,
  }).format(price);
}

function parseCandles(rows: unknown): BinanceCandle[] {
  if (!Array.isArray(rows)) {
    throw new Error("The market data response was invalid.");
  }

  const parsed: BinanceCandle[] = rows.map((row: unknown) => {
    if (!Array.isArray(row) || row.length < 5) {
      throw new Error("The market data response contained an invalid candle.");
    }

    const values = row as unknown[];
    const timestamp = Number(values[0]);
    const candle: BinanceCandle = {
      time: Math.floor(timestamp / 1000) as UTCTimestamp,
      open: Number(values[1]),
      high: Number(values[2]),
      low: Number(values[3]),
      close: Number(values[4]),
    };

    if (
      !Number.isFinite(timestamp) ||
      !Number.isFinite(candle.open) ||
      !Number.isFinite(candle.high) ||
      !Number.isFinite(candle.low) ||
      !Number.isFinite(candle.close)
    ) {
      throw new Error("Market data contained invalid prices.");
    }

    return candle;
  });

  return parsed;
}

export default function TradingChart() {
  const [symbol, setSymbol] = useState<TradingSymbol>("BTCUSDT");
  const [interval, setInterval] = useState<CandleInterval>("15m");
  const [candles, setCandles] = useState<BinanceCandle[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let cancelled = false;
    let requestInProgress = false;
    const controller = new AbortController();

    async function loadCandles() {
      if (requestInProgress || cancelled) {
        return;
      }

      requestInProgress = true;

      try {
        const response = await fetch(
          `https://data-api.binance.vision/api/v3/klines?symbol=${symbol}&interval=${interval}&limit=300`,
          { signal: controller.signal },
        );

        if (!response.ok) {
          throw new Error(
            `Market data request failed (${response.status}).`,
          );
        }

        const rows: unknown = await response.json();
        const parsed = parseCandles(rows);

        if (!cancelled) {
          setCandles(parsed);
          setError("");
          setLoading(false);
        }
      } catch (err) {
        if (
          !cancelled &&
          !(err instanceof DOMException && err.name === "AbortError")
        ) {
          setError(
            err instanceof Error
              ? err.message
              : "Unable to load market candles.",
          );
          setLoading(false);
        }
      } finally {
        requestInProgress = false;
      }
    }

    void loadCandles();

    const timer = window.setInterval(() => {
      void loadCandles();
    }, 15000);

    return () => {
      cancelled = true;
      controller.abort();
      window.clearInterval(timer);
    };
  }, [symbol, interval]);

  return (
    <section className="trading-chart-panel">
      <div className="trading-chart-header">
        <div>
          <p className="trading-chart-eyebrow">MARKET ANALYSIS</p>
          <h2>Candlestick chart</h2>
          <p className="trading-chart-subtitle">
            Live public exchange market data
          </p>
        </div>

        <label className="chart-symbol-select">
          <span>Market</span>
          <select
            value={symbol}
            onChange={(event) =>
              setSymbol(event.target.value as TradingSymbol)
            }
          >
            {SYMBOLS.map((item) => (
              <option key={item.value} value={item.value}>
                {item.label}
              </option>
            ))}
          </select>
        </label>
      </div>

      <div className="trading-chart-toolbar">
        <div className="chart-intervals" aria-label="Candle interval">
          {INTERVALS.map((item) => (
            <button
              type="button"
              key={item}
              className={interval === item ? "active" : ""}
              aria-pressed={interval === item}
              onClick={() => setInterval(item)}
            >
              {item}
            </button>
          ))}
        </div>

        <span className="chart-live-indicator">
          <span />
          Market feed
        </span>
      </div>

      <div className="trading-chart-price">
        <span>{symbol.replace("USDT", " / USDT")}</span>

        {candles.length > 0 && (
          <strong>
            {formatPrice(candles[candles.length - 1].close)} USDT
          </strong>
        )}
      </div>

      <ChartCanvas candles={candles} />

      {loading && <p className="chart-message">Loading candles…</p>}

      {!loading && error && (
        <p className="chart-message chart-error" role="alert">
          {error} Check your internet connection and try again.
        </p>
      )}

      {!loading && !error && candles.length === 0 && (
        <p className="chart-message">No candle data is available.</p>
      )}

      <div className="trading-chart-footer">
        <span>Source: Binance public market data</span>
        <a
          href="https://www.tradingview.com/"
          target="_blank"
          rel="noreferrer"
        >
          Charts by TradingView
        </a>
      </div>
    </section>
  );
}

function ChartCanvas({ candles }: { candles: BinanceCandle[] }) {
  const containerRef = useRef<HTMLDivElement | null>(null);

  // Use Time here so the series ref matches createChart's inferred type.
  const seriesRef = useRef<ISeriesApi<"Candlestick", Time> | null>(null);

  useEffect(() => {
    const container = containerRef.current;

    if (!container) {
      return;
    }

    const chart = createChart(container, {
      autoSize: true,
      height: 390,
      layout: {
        background: {
          type: ColorType.Solid,
          color: "#11151d",
        },
        textColor: "#8994a7",
        fontFamily: "DM Sans, sans-serif",
      },
      grid: {
        vertLines: { color: "#202633" },
        horzLines: { color: "#202633" },
      },
      rightPriceScale: {
        borderColor: "#2a3241",
      },
      timeScale: {
        borderColor: "#2a3241",
        timeVisible: true,
        secondsVisible: false,
      },
      crosshair: {
        vertLine: {
          color: "#667085",
          labelBackgroundColor: "#30394a",
        },
        horzLine: {
          color: "#667085",
          labelBackgroundColor: "#30394a",
        },
      },
    });

    const series = chart.addSeries(CandlestickSeries, {
      upColor: "#16c784",
      downColor: "#ea3943",
      borderVisible: false,
      wickUpColor: "#16c784",
      wickDownColor: "#ea3943",
      priceLineVisible: true,
    });

    seriesRef.current = series;

    return () => {
      seriesRef.current = null;
      chart.remove();
    };
  }, []);

  useEffect(() => {
    const series = seriesRef.current;

    if (!series || candles.length === 0) {
      return;
    }

    // CandlestickData<Time> is compatible with the series' inferred time type.
    const data: CandlestickData<Time>[] = candles.map((candle) => ({
      time: candle.time,
      open: candle.open,
      high: candle.high,
      low: candle.low,
      close: candle.close,
    }));

    series.setData(data);
  }, [candles]);

  return <div className="trading-chart-canvas" ref={containerRef} />;
}