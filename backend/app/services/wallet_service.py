from app.extensions import db
from app.models import Wallet
from app.services.asset_service import initialize_wallet_balances


def create_wallet(
    user_id: int,
    name: str,
    base_currency: str = "USD",
) -> Wallet:
    wallet = Wallet(
        user_id=user_id,
        name=name,
        base_currency=base_currency,
    )

    try:
        db.session.add(wallet)
        db.session.flush()

        initialize_wallet_balances(wallet.id, commit=False)

        # Commit wallet and balances together.
        db.session.commit()
        return wallet

    except Exception:
        db.session.rollback()
        raise


def list_user_wallets(user_id: int) -> list[Wallet]:
    return (
        Wallet.query
        .filter_by(user_id=user_id)
        .order_by(Wallet.created_at.desc())
        .all()
    )
