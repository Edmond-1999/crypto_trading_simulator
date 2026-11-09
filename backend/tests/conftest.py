
import pytest
from decimal import Decimal

from app import create_app
from app.extensions import db
from app.models import (
    Asset,
    Balance,
    LedgerEntry,
    TradeOrder,
    User,
    Wallet,
)
from app.services.asset_service import (
    seed_default_assets,
    initialize_wallet_balances,
)


@pytest.fixture()
def app():
    app = create_app({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite://",
        "JWT_SECRET_KEY": "pytest-only-secret-key-for-automated-tests-2026",
    })

    with app.app_context():
        db.create_all()
        seed_default_assets()

        yield app

        db.session.remove()
        db.drop_all()


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def trading_wallet(app):
    with app.app_context():
        user = User(
            email="trader@example.test",
            password_hash="test-only-password-hash",
        )
        db.session.add(user)
        db.session.flush()

        wallet = Wallet(
            user_id=user.id,
            name="Test Wallet",
            base_currency="USD",
        )
        db.session.add(wallet)
        db.session.flush()

        initialize_wallet_balances(wallet.id, commit=False)

        assets = {
            asset.symbol: asset
            for asset in db.session.execute(
                db.select(Asset)
            ).scalars()
        }

        balances = {
            balance.asset.symbol: balance
            for balance in db.session.execute(
                db.select(Balance).where(
                    Balance.wallet_id == wallet.id
                )
            ).scalars()
        }

        balances["USD"].available = Decimal("1000")
        balances["USDT"].available = Decimal("1000")
        balances["BTC"].available = Decimal("0.01")
        balances["ETH"].available = Decimal("1")

        db.session.commit()

        return {
            "user_id": user.id,
            "wallet_id": wallet.id,
            "assets": {
                symbol: asset.id
                for symbol, asset in assets.items()
            },
        }
