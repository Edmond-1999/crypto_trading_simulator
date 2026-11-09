
from flask import Blueprint, jsonify
from flask_jwt_extended import get_jwt_identity, jwt_required
from sqlalchemy import select

from app.extensions import db
from app.models import Balance, Asset, Wallet

balances_bp = Blueprint(
    "balances",
    __name__,
    url_prefix="/api/v1/wallets",
)


@balances_bp.get("/<int:wallet_id>/balances")
@jwt_required()
def get_wallet_balances(wallet_id):
    user_id = int(get_jwt_identity())

    wallet = db.session.execute(
        select(Wallet).where(
            Wallet.id == wallet_id,
            Wallet.user_id == user_id,
        )
    ).scalar_one_or_none()

    if wallet is None:
        return jsonify({"error": "Wallet not found."}), 404

    rows = db.session.execute(
        select(Balance, Asset)
        .join(Asset, Balance.asset_id == Asset.id)
        .where(Balance.wallet_id == wallet.id)
        .order_by(Asset.symbol)
    ).all()

    balances = [
        {
            "asset": asset.symbol,
            "available": str(balance.available),
            "reserved": str(balance.reserved),
            "total": str(balance.available + balance.reserved),
        }
        for balance, asset in rows
    ]

    return jsonify({
        "wallet_id": wallet.id,
        "wallet_name": wallet.name,
        "base_currency": wallet.base_currency,
        "balances": balances,
    }), 200
