
from decimal import Decimal, ROUND_HALF_UP

import pytest

from app.extensions import db
from app.models import (
    Balance,
    LedgerEntry,
    PositionCostBasis,
    TradeOrder,
)
from app.services import trading_service
from app.services.trading_service import (
    TradingError,
    execute_market_order,
)


# SQLite can introduce tiny floating-point artifacts when storing NUMERIC.
def money(value):
    return Decimal(str(value)).quantize(
        Decimal("0.00000001"),
        rounding=ROUND_HALF_UP,
    )


@pytest.fixture(autouse=True)
def fixed_market_price(monkeypatch):
    monkeypatch.setattr(
        trading_service,
        "get_market_price",
        lambda base, quote: Decimal("100"),
    )

    # USD-denominated tests don't need a USDT conversion.
    monkeypatch.setattr(
        trading_service,
        "get_usdt_usd_rate",
        lambda: Decimal("1"),
        raising=False,
    )


def execute(
    wallet,
    side,
    quantity,
    user_id=None,
    base_symbol="BTC",
    quote_symbol="USD",
):
    return execute_market_order(
        user_id=user_id or wallet["user_id"],
        wallet_id=wallet["wallet_id"],
        base_symbol=base_symbol,
        quote_symbol=quote_symbol,
        side=side,
        raw_quantity=quantity,
    )


def balance_amount(wallet_id, symbol):
    from app.models import Asset

    balance = db.session.execute(
        db.select(Balance)
        .join(Asset, Balance.asset_id == Asset.id)
        .where(
            Balance.wallet_id == wallet_id,
            Asset.symbol == symbol,
        )
    ).scalar_one()

    return Decimal(str(balance.available))


def position(wallet, symbol="BTC"):
    from app.models import Asset

    return db.session.execute(
        db.select(PositionCostBasis)
        .join(Asset, PositionCostBasis.asset_id == Asset.id)
        .where(
            PositionCostBasis.wallet_id == wallet["wallet_id"],
            Asset.symbol == symbol,
        )
    ).scalar_one()


def test_buy_updates_balances_and_ledger(app, trading_wallet):
    with app.app_context():
        wallet = trading_wallet

        order = execute(wallet, "BUY", "1")

        assert money(order.quote_amount) == money("100")
        assert money(order.fee) == money("0.1")
        assert order.status == "filled"

        assert money(
            balance_amount(wallet["wallet_id"], "USD")
        ) == money("899.9")

        assert money(
            balance_amount(wallet["wallet_id"], "BTC")
        ) == money("1.01")

        entries = db.session.execute(
            db.select(LedgerEntry).where(
                LedgerEntry.wallet_id == wallet["wallet_id"]
            )
        ).scalars().all()

        assert len(entries) == 3

        usd_ledger_total = sum(
            (
                Decimal(str(entry.amount))
                for entry in entries
                if entry.asset_id == wallet["assets"]["USD"]
            ),
            Decimal("0"),
        )

        assert money(usd_ledger_total) == money("-100.1")


def test_buy_tracks_cost_including_fee(app, trading_wallet):
    with app.app_context():
        wallet = trading_wallet

        # The fixture's original 0.01 BTC has unknown historical cost.
        execute(wallet, "BUY", "1")

        tracked = position(wallet)

        assert money(tracked.known_quantity) == money("1")
        assert money(tracked.known_cost_basis_usd) == money("100.1")
        assert money(tracked.unknown_quantity) == money("0.01")


def test_sell_updates_balances_and_ledger(app, trading_wallet):
    with app.app_context():
        wallet = trading_wallet

        order = execute(wallet, "SELL", "0.005")

        assert money(order.quote_amount) == money("0.5")
        assert money(order.fee) == money("0.0005")

        assert money(
            balance_amount(wallet["wallet_id"], "BTC")
        ) == money("0.005")

        assert money(
            balance_amount(wallet["wallet_id"], "USD")
        ) == money("1000.4995")

        entries = db.session.execute(
            db.select(LedgerEntry).where(
                LedgerEntry.wallet_id == wallet["wallet_id"]
            )
        ).scalars().all()

        assert len(entries) == 3


def test_selling_unknown_cost_units_does_not_invent_pnl(
    app,
    trading_wallet,
):
    with app.app_context():
        wallet = trading_wallet

        order = execute(wallet, "SELL", "0.005")

        # The fixture's original BTC has no known acquisition cost.
        assert order.realized_pnl_usd is not None
        assert money(order.realized_pnl_usd) == money("0")
        assert order.realized_pnl_complete is False

        tracked = position(wallet)
        assert money(tracked.unknown_quantity) == money("0.005")
        assert money(tracked.known_quantity) == money("0")


def test_sell_unknown_units_first_then_realize_known_pnl(
    app,
    trading_wallet,
):
    with app.app_context():
        wallet = trading_wallet

        # Buy one BTC at $100 plus a $0.10 fee.
        execute(wallet, "BUY", "1")

        # Sell 0.015 BTC: first disposes of the fixture's 0.01 BTC
        # unknown-cost position, then 0.005 BTC with known cost basis.
        order = execute(wallet, "SELL", "0.015")

        assert order.realized_pnl_complete is False

        # Known average acquisition cost = $100.10 per BTC.
        # Net sell proceeds = $1.50 - $0.0015 = $1.4985.
        # Proceeds allocated to 0.005 known BTC = $0.4995.
        # Realized P&L on known BTC = $0.4995 - $0.5005 = -$0.001.
        assert money(order.realized_pnl_usd) == money("-0.001")

        tracked = position(wallet)
        assert money(tracked.unknown_quantity) == money("0")
        assert money(tracked.known_quantity) == money("0.995")
        assert money(tracked.known_cost_basis_usd) == money("99.5995")


def test_sell_known_cost_position_calculates_realized_pnl(
    app,
    trading_wallet,
):
    with app.app_context():
        wallet = trading_wallet

        # Sell the entire unknown position first, leaving no unknown units.
        execute(wallet, "SELL", "0.01")

        # Buy one BTC at $100 plus $0.10 fee.
        execute(wallet, "BUY", "1")

        # Sell 0.5 BTC at $100. The allocated acquisition cost is $50.05
        # and net proceeds are $49.95, resulting in -$0.10 realized P&L.
        order = execute(wallet, "SELL", "0.5")

        assert order.realized_pnl_complete is True
        assert money(order.realized_pnl_usd) == money("-0.1")

        tracked = position(wallet)
        assert money(tracked.known_quantity) == money("0.5")
        assert money(tracked.known_cost_basis_usd) == money("50.05")
        assert money(tracked.unknown_quantity) == money("0")


@pytest.mark.parametrize(
    "quantity",
    [
        "0",
        "-1",
        "NaN",
        "Infinity",
        "not-a-number",
        "0.0000000000000000001",
    ],
)
def test_invalid_quantity_is_rejected(app, trading_wallet, quantity):
    with app.app_context():
        wallet = trading_wallet

        with pytest.raises(TradingError):
            execute(wallet, "BUY", quantity)

        orders = db.session.execute(
            db.select(TradeOrder).where(
                TradeOrder.wallet_id == wallet["wallet_id"]
            )
        ).scalars().all()

        assert orders == []


def test_buy_with_insufficient_funds_rolls_back(app, trading_wallet):
    with app.app_context():
        wallet = trading_wallet

        with pytest.raises(TradingError, match="Insufficient USD balance"):
            execute(wallet, "BUY", "11")

        assert money(
            balance_amount(wallet["wallet_id"], "USD")
        ) == money("1000")

        assert money(
            balance_amount(wallet["wallet_id"], "BTC")
        ) == money("0.01")

        orders = db.session.execute(
            db.select(TradeOrder).where(
                TradeOrder.wallet_id == wallet["wallet_id"]
            )
        ).scalars().all()

        entries = db.session.execute(
            db.select(LedgerEntry).where(
                LedgerEntry.wallet_id == wallet["wallet_id"]
            )
        ).scalars().all()

        assert orders == []
        assert entries == []


def test_insufficient_funds_does_not_change_cost_basis(
    app,
    trading_wallet,
):
    with app.app_context():
        wallet = trading_wallet

        with pytest.raises(TradingError, match="Insufficient USD balance"):
            execute(wallet, "BUY", "11")

        # A failed trade must not create a cost-basis record.
        tracked = db.session.execute(
            db.select(PositionCostBasis).where(
                PositionCostBasis.wallet_id == wallet["wallet_id"],
                PositionCostBasis.asset_id == wallet["assets"]["BTC"],
            )
        ).scalar_one_or_none()

        assert tracked is None


def test_cannot_trade_from_another_users_wallet(app, trading_wallet):
    with app.app_context():
        wallet = trading_wallet

        with pytest.raises(TradingError, match="Wallet not found"):
            execute(
                wallet,
                "BUY",
                "0.001",
                user_id=wallet["user_id"] + 9999,
            )

        orders = db.session.execute(
            db.select(TradeOrder).where(
                TradeOrder.wallet_id == wallet["wallet_id"]
            )
        ).scalars().all()

        assert orders == []
