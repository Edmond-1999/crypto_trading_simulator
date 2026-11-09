
from flask import Blueprint, jsonify

from app.services.market_price_service import (
    MarketPriceError,
    get_market_price,
    get_usdt_usd_rate,
)


market_bp = Blueprint(
    "market",
    __name__,
    url_prefix="/api/v1/market",
)


@market_bp.get("/prices")
def get_prices():
    try:
        usdt_usd = get_usdt_usd_rate()

        prices = {
            "BTC": {
                "USDT": str(get_market_price("BTC", "USDT")),
                "USD": str(get_market_price("BTC", "USDT") * usdt_usd),
            },
            "ETH": {
                "USDT": str(get_market_price("ETH", "USDT")),
                "USD": str(get_market_price("ETH", "USDT") * usdt_usd),
            },
        }

        return jsonify({
            "source": "Binance + Coinbase",
            "usdt_usd_rate": str(usdt_usd),
            "prices": prices,
        }), 200

    except MarketPriceError as exc:
        return jsonify({
            "error": str(exc),
        }), 503
