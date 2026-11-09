
from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from app.services.wallet_service import create_wallet, list_user_wallets

wallets_bp = Blueprint("wallets", __name__, url_prefix="/api/v1/wallets")

SUPPORTED_CURRENCIES = {"USD", "USDT"}


def serialize_wallet(wallet):
    return {
        "id": wallet.id,
        "name": wallet.name,
        "base_currency": wallet.base_currency,
        "created_at": wallet.created_at.isoformat(),
    }


@wallets_bp.post("")
@jwt_required()
def create_wallet_route():
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({"error": "Request body must be a JSON object."}), 400

    name = data.get("name")
    currency = data.get("base_currency", "USD")

    if not isinstance(name, str) or not name.strip():
        return jsonify({"error": "Wallet name is required."}), 400

    name = name.strip()
    if len(name) > 100:
        return jsonify({"error": "Wallet name must be 100 characters or fewer."}), 400

    if not isinstance(currency, str):
        return jsonify({"error": "base_currency must be a string."}), 400

    currency = currency.strip().upper()
    if currency not in SUPPORTED_CURRENCIES:
        return jsonify({
            "error": "Unsupported base currency.",
            "supported_currencies": sorted(SUPPORTED_CURRENCIES),
        }), 400

    user_id = int(get_jwt_identity())

    wallet = create_wallet(
        user_id=user_id,
        name=name,
        base_currency=currency,
    )

    return jsonify({"wallet": serialize_wallet(wallet)}), 201


@wallets_bp.get("")
@jwt_required()
def get_wallets_route():
    user_id = int(get_jwt_identity())
    wallets = list_user_wallets(user_id)

    return jsonify({
        "wallets": [serialize_wallet(wallet) for wallet in wallets]
    }), 200
