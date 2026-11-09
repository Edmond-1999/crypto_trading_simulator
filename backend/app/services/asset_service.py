
from app.extensions import db
from app.models import Asset, Balance, Wallet

DEFAULT_ASSETS = [
    {"symbol": "USD", "name": "US Dollar", "asset_type": "fiat"},
    {"symbol": "USDT", "name": "Tether", "asset_type": "crypto"},
    {"symbol": "BTC", "name": "Bitcoin", "asset_type": "crypto"},
    {"symbol": "ETH", "name": "Ethereum", "asset_type": "crypto"},
]


def seed_default_assets():
    """Create default assets if they do not already exist."""
    for item in DEFAULT_ASSETS:
        asset = Asset.query.filter_by(symbol=item["symbol"]).first()

        if asset is None:
            db.session.add(Asset(**item))

    db.session.commit()


def initialize_wallet_balances(wallet_id: int, commit: bool):
    """Create zero balances for active assets without duplicating rows."""
    wallet = db.session.get(Wallet, wallet_id)

    if wallet is None:
        raise ValueError("Wallet not found.")

    assets = Asset.query.filter_by(is_active=True).all()

    for asset in assets:
        existing = Balance.query.filter_by(
            wallet_id=wallet.id,
            asset_id=asset.id,
        ).first()

        if existing is None:
            db.session.add(
                Balance(
                    wallet_id=wallet.id,
                    asset_id=asset.id,
                    available=0,
                    reserved=0,
                )
            )

    if commit:
        db.session.commit()
