from decimal import Decimal, InvalidOperation

import requests


BINANCE_TICKER_URL = "https://data-api.binance.vision/api/v3/ticker/price"
COINBASE_TICKER_URL = (
    "https://api.exchange.coinbase.com/products/USDT-USD/ticker"
)

SUPPORTED_BASE_ASSETS = {"BTC", "ETH"}
SUPPORTED_QUOTE_ASSETS = {"USD", "USDT"}


class MarketPriceError(Exception):
    pass


def _get_positive_price(url, params=None):
    try:
        response = requests.get(
            url,
            params=params,
            timeout=(3, 5),
            headers={"User-Agent": "CryptoCurrencyApp/1.0"},
        )
        response.raise_for_status()
        data = response.json()

        if not isinstance(data, dict) or "price" not in data:
            raise MarketPriceError(
                "Price provider returned an unexpected response."
            )

        price = Decimal(str(data["price"]))

        if not price.is_finite() or price <= 0:
            raise MarketPriceError(
                "Price provider returned an invalid price."
            )

        return price

    except MarketPriceError:
        raise
    except (
        requests.RequestException,
        ValueError,
        TypeError,
        KeyError,
        InvalidOperation,
    ) as exc:
        raise MarketPriceError(
            "Live market prices are temporarily unavailable."
        ) from exc


def get_usdt_usd_rate():
    # Coinbase returns a single ticker object containing "price".
    return _get_positive_price(COINBASE_TICKER_URL)


def get_market_price(base_symbol, quote_symbol):
    base_symbol = str(base_symbol).strip().upper()
    quote_symbol = str(quote_symbol).strip().upper()

    if base_symbol not in SUPPORTED_BASE_ASSETS:
        raise MarketPriceError("Unsupported base asset.")

    if quote_symbol not in SUPPORTED_QUOTE_ASSETS:
        raise MarketPriceError("Unsupported quote currency.")

    # Request a specific Binance symbol, not the entire ticker list.
    usdt_price = _get_positive_price(
        BINANCE_TICKER_URL,
        params={"symbol": f"{base_symbol}USDT"},
    )

    if quote_symbol == "USDT":
        return usdt_price

    usdt_usd_rate = get_usdt_usd_rate()
    return usdt_price * usdt_usd_rate