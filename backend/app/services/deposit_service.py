from decimal import Decimal, InvalidOperation
from uuid import uuid4

from sqlalchemy import select

from app.extensions import db
from app.models import Asset, Balance, LedgerEntry, Wallet
from app.services.pnl_service import get_or_create_position


class DepositError(Exception):
    pass


def simulate_deposit(
    user_id: int,
    wallet_id: int,
    asset_symbol: str,
    amount,
) -> LedgerEntry:
    try:
        value = Decimal(str(amount))
    except (InvalidOperation, ValueError, TypeError):
        raise DepositError("Amount must be a valid decimal number.")

    if not value.is_finite() or value <= 0:
        raise DepositError("Amount must be greater than zero.")

    if not isinstance(asset_symbol, str) or not asset_symbol.strip():
        raise DepositError("Asset symbol is required.")

    asset_symbol = asset_symbol.strip().upper()

    try:
        # Lock the wallet row so concurrent deposits for this wallet serialize.
        wallet = db.session.execute(
            select(Wallet)
            .where(
                Wallet.id == wallet_id,
                Wallet.user_id == user_id,
            )
            .with_for_update()
        ).scalar_one_or_none()

        if wallet is None:
            raise DepositError("Wallet not found.")

        asset = db.session.execute(
            select(Asset).where(
                Asset.symbol == asset_symbol,
                Asset.is_active.is_(True),
            )
        ).scalar_one_or_none()

        if asset is None:
            raise DepositError("Asset not found or inactive.")

        balance = db.session.execute(
            select(Balance)
            .where(
                Balance.wallet_id == wallet.id,
                Balance.asset_id == asset.id,
            )
            .with_for_update()
        ).scalar_one_or_none()

        if balance is None:
            raise DepositError(
                "Wallet has no balance entry for this asset."
            )

        # Deposited crypto has no acquisition history in this simulator. Track
        # BTC/ETH deposits as unknown-cost units so P&L never invents a basis.
        if asset_symbol in {"BTC", "ETH"}:
            position = get_or_create_position(wallet.id, asset.id)
            position.unknown_quantity = (
                Decimal(position.unknown_quantity) + value
            )

        balance.available = Decimal(balance.available) + value

        entry = LedgerEntry(
            wallet_id=wallet.id,
            asset_id=asset.id,
            entry_type="simulated_deposit",
            amount=value,
            reference=f"sim-deposit-wallet-{wallet.id}-{uuid4().hex}",
        )

        db.session.add(entry)
        db.session.flush()
        db.session.commit()

        return entry

    except Exception:
        db.session.rollback()
        raise