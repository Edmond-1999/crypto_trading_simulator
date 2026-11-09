from flask import Blueprint, current_app, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required
from sqlalchemy import select

from app.extensions import db
from app.models import TradeOrder, Wallet
from app.services.trading_service import (
    TradingError,
    execute_market_order,
)


orders_bp = Blueprint(
    "orders",
    __name__,
    url_prefix="/api/v1/wallets",
)


def serialize_order(order):
    return {
        "id": order.id,
        "wallet_id": order.wallet_id,
        "base_asset_id": order.base_asset_id,
        "quote_asset_id": order.quote_asset_id,
        "side": order.side,
        "type": order.order_type,
        "quantity": str(order.quantity),
        "price": str(order.price),
        "quote_amount": str(order.quote_amount),
        "fee_amount": str(order.fee),
        "fee_rate": str(order.fee_rate),
        "price_source": order.price_source,
        "status": order.status,
        "realized_pnl_usd": (
            str(order.realized_pnl_usd)
            if order.realized_pnl_usd is not None
            else None
        ),
        "realized_pnl_complete": order.realized_pnl_complete,
        "created_at": order.created_at.isoformat(),
    }


@orders_bp.post("/<int:wallet_id>/orders")
@jwt_required()
def create_market_order(wallet_id):
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({
            "error": "Request body must be a JSON object."
        }), 400

    base_asset = data.get("base_asset")
    quote_currency = data.get("quote_currency")
    side = data.get("side")
    quantity = data.get("quantity")

    if quantity is None or isinstance(quantity, bool):
        return jsonify({"error": "Quantity is required."}), 400

    try:
        order = execute_market_order(
            user_id=int(get_jwt_identity()),
            wallet_id=wallet_id,
            base_symbol=base_asset,
            quote_symbol=quote_currency,
            side=side,
            raw_quantity=quantity,
        )
    except TradingError as exc:
        message = str(exc)

        if message == "Wallet not found.":
            status = 404
        elif "temporarily unavailable" in message.lower():
            status = 503
        else:
            status = 400

        return jsonify({"error": message}), status
    except Exception:
        current_app.logger.exception(
            "Failed to execute simulated market order"
        )
        return jsonify({
            "error": "Order could not be processed."
        }), 500

    return jsonify({
        "message": "Simulated market order filled.",
        "order": serialize_order(order),
    }), 201


@orders_bp.get("/<int:wallet_id>/orders")
@jwt_required()
def list_market_orders(wallet_id):
    user_id = int(get_jwt_identity())

    wallet = db.session.execute(
        select(Wallet).where(
            Wallet.id == wallet_id,
            Wallet.user_id == user_id,
        )
    ).scalar_one_or_none()

    if wallet is None:
        return jsonify({"error": "Wallet not found."}), 404

    orders = db.session.execute(
        select(TradeOrder)
        .where(TradeOrder.wallet_id == wallet.id)
        .order_by(
            TradeOrder.created_at.desc(),
            TradeOrder.id.desc(),
        )
        .limit(100)
    ).scalars().all()

    return jsonify({
        "wallet_id": wallet.id,
        "orders": [serialize_order(order) for order in orders],
    }), 200