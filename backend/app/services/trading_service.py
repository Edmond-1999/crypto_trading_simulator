
from decimal import (
    Decimal,
    InvalidOperation,
    ROUND_HALF_UP,
    localcontext,
)
from uuid import uuid4

from sqlalchemy import select

from app.extensions import db
from app.models import Asset, Balance, LedgerEntry, TradeOrder, Wallet
from app.services.market_price_service import (
    MarketPriceError,
    get_market_price,
    get_usdt_usd_rate,
)
from app.services.pnl_service import record_buy, record_sell


FEE_RATE = Decimal("0.001")
DECIMAL_QUANTUM = Decimal("0.000000000000000001")


class TradingError(Exception):
    pass


def _parse_quantity(raw_quantity):
    try:
        quantity = Decimal(str(raw_quantity))
    except (InvalidOperation, ValueError, TypeError):
        raise TradingError("Quantity must be a valid decimal number.")

    if not quantity.is_finite() or quantity <= 0:
        raise TradingError("Quantity must greater than zero.")

    if quantity.as_tuple().exponent < -18:
        raise TradingError(
            "Quantity supports at most 18 decimal places."
        )

    if quantity.adjusted() > 17:
        raise TradingError("Quantity is too large.")

    return quantity


def _money(value):
    return value.quantize(
        DECIMAL_QUANTUM,
        rounding=ROUND_HALF_UP,
    )


def execute_market_order(
    user_id,
    wallet_id,
    base_symbol,
    quote_symbol,
    side,
    raw_quantity,
):
    base_symbol = (
        base_symbol.strip().upper()
        if isinstance(base_symbol, str)
        else ""
    )

    quote_symbol = (
        quote_symbol.strip().upper()
        if isinstance(quote_symbol, str)
        else ""
    )

    side = side.strip().upper() if isinstance(side, str) else ""

    if base_symbol not in {"BTC", "ETH"}:
        raise TradingError("Base asset must be BTC or ETH.")

    if quote_symbol not in {"USD", "USDT"}:
        raise TradingError("Quote asset must be USD or USDT.")

    if side not in {"BUY", "SELL"}:
        raise TradingError("Side must be BUY or SELL.")

    quantity = _parse_quantity(raw_quantity)

    # Fetch market data before starting the database transaction.
    try:
        price = get_market_price(base_symbol, quote_symbol)

        usd_conversion_rate = (
            Decimal("1")
            if quote_symbol == "USD"
            else get_usdt_usd_rate()
        )
    except MarketPriceError as exc:
        raise TradingError(str(exc)) from exc

    with localcontext() as context:
        context.prec = 60

        price = _money(price)
        gross = _money(quantity * price)
        fee = _money(gross * FEE_RATE)

        gross_usd = _money(gross * usd_conversion_rate)
        fee_usd = _money(fee * usd_conversion_rate)

    if price <= 0 or gross <= 0:
        raise TradingError("Order value is too small to execute.")

    if usd_conversion_rate <= 0:
        raise TradingError("USD conversion rate is invalid.")

    try:
        # Lock the wallet and ensure it belongs to the logged-in user.
        wallet = db.session.execute(
            select(Wallet)
            .where(
                Wallet.id == wallet_id,
                Wallet.user_id == user_id,
            )
            .with_for_update()
        ).scalar_one_or_none()

        if wallet is None:
            raise TradingError("Wallet not found.")

        # Lock assets in a consistent order.
        assets = db.session.execute(
            select(Asset)
            .where(
                Asset.symbol.in_([base_symbol, quote_symbol]),
                Asset.is_active.is_(True),
            )
            .order_by(Asset.id)
        ).scalars().all()

        asset_by_symbol = {asset.symbol: asset for asset in assets}
        base_asset = asset_by_symbol.get(base_symbol)
        quote_asset = asset_by_symbol.get(quote_symbol)

        if base_asset is None or quote_asset is None:
            raise TradingError("One or more assets are not available.")

        # Lock both balance rows in asset-ID order.
        balance_rows = db.session.execute(
            select(Balance)
            .where(
                Balance.wallet_id == wallet.id,
                Balance.asset_id.in_(
                    [base_asset.id, quote_asset.id]
                ),
            )
            .order_by(Balance.asset_id)
            .with_for_update()
        ).scalars().all()

        balance_by_asset = {
            balance.asset_id: balance for balance in balance_rows
        }

        base_balance = balance_by_asset.get(base_asset.id)
        quote_balance = balance_by_asset.get(quote_asset.id)

        if base_balance is None or quote_balance is None:
            raise TradingError(
                "Wallet balance entries are missing for this trade."
            )

        order = TradeOrder(
            wallet_id=wallet.id,
            base_asset_id=base_asset.id,
            quote_asset_id=quote_asset.id,
            side=side,
            order_type="market",
            quantity=quantity,
            price=price,
            quote_amount=gross,
            fee=fee,
            fee_rate=FEE_RATE,
            price_source=(
                "Binance+Coinbase"
                if quote_symbol == "USD"
                else "Binance"
            ),
            status="filled",
            realized_pnl_usd=(
                Decimal("0") if side == "BUY" else None
            ),
            realized_pnl_complete=True,
        )

        db.session.add(order)
        db.session.flush()

        reference_prefix = f"sim-trade-{order.id}-{uuid4().hex}"

        if side == "BUY":
            total_cost = gross + fee

            if quote_balance.available < total_cost:
                raise TradingError(
                    f"Insufficient {quote_symbol} balance. "
                    f"Required including fee: {total_cost}."
                )

            # Record cost basis BEFORE increasing the balance. If this is the
            # first cost-basis record, the service reads the pre-trade balance
            # and classifies those existing units as unknown-cost inventory.
            record_buy(
                wallet_id=wallet.id,
                asset_id=base_asset.id,
                quantity=quantity,
                gross_usd=gross_usd,
                fee_usd=fee_usd,
            )

            quote_balance.available = (
                Decimal(quote_balance.available) - gross - fee
            )

            base_balance.available = (
                Decimal(base_balance.available) + quantity
            )

            entries = [
                LedgerEntry(
                    wallet_id=wallet.id,
                    asset_id=quote_asset.id,
                    entry_type="trade_buy_debit",
                    amount=-gross,
                    reference=f"{reference_prefix}-quote",
                ),
                LedgerEntry(
                    wallet_id=wallet.id,
                    asset_id=quote_asset.id,
                    entry_type="trade_fee",
                    amount=-fee,
                    reference=f"{reference_prefix}-fee",
                ),
                LedgerEntry(
                    wallet_id=wallet.id,
                    asset_id=base_asset.id,
                    entry_type="trade_buy_credit",
                    amount=quantity,
                    reference=f"{reference_prefix}-base",
                ),
            ]

        else:
            if base_balance.available < quantity:
                raise TradingError(
                    f"Insufficient {base_symbol} balance."
                )

            net_proceeds = gross - fee

            if net_proceeds <= 0:
                raise TradingError(
                    "Order proceeds must exceed the fee."
                )

            # Record cost basis BEFORE reducing the balance, so any missing
            # position record sees the original holdings, not the reduced one.
            realized_pnl, pnl_complete = record_sell(
                wallet_id=wallet.id,
                asset_id=base_asset.id,
                quantity=quantity,
                gross_usd=gross_usd,
                fee_usd=fee_usd,
            )

            base_balance.available = (
                Decimal(base_balance.available) - quantity
            )

            quote_balance.available = (
                Decimal(quote_balance.available) + net_proceeds
            )

            order.realized_pnl_usd = realized_pnl
            order.realized_pnl_complete = pnl_complete

            entries = [
                LedgerEntry(
                    wallet_id=wallet.id,
                    asset_id=base_asset.id,
                    entry_type="trade_sell_debit",
                    amount=-quantity,
                    reference=f"{reference_prefix}-base",
                ),
                LedgerEntry(
                    wallet_id=wallet.id,
                    asset_id=quote_asset.id,
                    entry_type="trade_sell_credit",
                    amount=gross,
                    reference=f"{reference_prefix}-quote",
                ),
                LedgerEntry(
                    wallet_id=wallet.id,
                    asset_id=quote_asset.id,
                    entry_type="trade_fee",
                    amount=-fee,
                    reference=f"{reference_prefix}-fee",
                ),
            ]

        db.session.add_all(entries)
        db.session.commit()

        return order

    except Exception:
        db.session.rollback()
        raise
