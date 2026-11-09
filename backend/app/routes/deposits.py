
from decimal import Decimal, InvalidOperation

from flask import Blueprint, jsonify, request, current_app
from flask_jwt_extended import get_jwt_identity, jwt_required

from app.services.deposit_service import (
    DepositError,
    simulate_deposit,
)

deposits_bp = Blueprint(
    "deposits",
    __name__,
    url_prefix="/api/v1/wallets",
)


@deposits_bp.post("/<int:wallet_id>/deposits")
@jwt_required()
def create_simulated_deposit(wallet_id):
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({"error": "Request body must be a JSON object."}), 400

    symbol = data.get("asset")
    raw_amount = data.get("amount")

    if not isinstance(symbol, str) or not symbol.strip():
        return jsonify({"error": "Asset symbol is required."}), 400

    if raw_amount is None or isinstance(raw_amount, bool):
        return jsonify({"error": "Amount is required and must be numeric."}), 400

    try:
        amount = Decimal(str(raw_amount))
    except (InvalidOperation, ValueError, TypeError):
        return jsonify({"error": "Amount must be a valid decimal number."}), 400

    if not amount.is_finite() or amount <= 0:
        return jsonify({"error": "Amount must be greater than zero."}), 400

    try:
        entry = simulate_deposit(
            user_id=int(get_jwt_identity()),
            wallet_id=wallet_id,
            asset_symbol=symbol,
            amount=amount,
        )
    except DepositError as exc:
        message = str(exc)
        status = 404 if message in {
            "Wallet not found.",
            "Asset not found or inactive.",
        } else 400
        return jsonify({"error": message}), status
    except Exception:
        current_app.logger.exception(
            "Failed to process simulated deposit"
        )
        return jsonify({
            "error": "Deposit could not be processed."
        }), 500

    return jsonify({
        "message": "Simulated deposit completed.",
        "deposit": {
            "id": entry.id,
            "wallet_id": entry.wallet_id,
            "asset": symbol.strip().upper(),
            "amount": str(entry.amount),
            "entry_type": entry.entry_type,
            "created_at": entry.created_at.isoformat(),
        },
    }), 201
