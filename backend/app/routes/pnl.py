from flask import Blueprint, current_app, jsonify
from flask_jwt_extended import get_jwt_identity, jwt_required
from sqlalchemy import select

from app.extensions import db
from app.models import Wallet
from app.services.pnl_service import get_wallet_pnl


pnl_bp = Blueprint(
    "pnl",
    __name__,
    url_prefix="/api/v1/wallets",
)


@pnl_bp.get("/<int:wallet_id>/pnl")
@jwt_required()
def wallet_pnl(wallet_id):
    user_id = int(get_jwt_identity())

    wallet = db.session.execute(
        select(Wallet).where(
            Wallet.id == wallet_id,
            Wallet.user_id == user_id,
        )
    ).scalar_one_or_none()

    if wallet is None:
        return jsonify({"error": "Wallet not found."}), 404

    try:
        result = get_wallet_pnl(wallet.id)
        return jsonify(result), 200
    except Exception:
        db.session.rollback()
        current_app.logger.exception(
            "Failed to calculate wallet P&L"
        )
        return jsonify({
            "error": "P&L could not be calculated."
        }), 500