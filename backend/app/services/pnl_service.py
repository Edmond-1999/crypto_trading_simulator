from decimal import Decimal, localcontext

from sqlalchemy import func, select

from app.extensions import db
from app.models import Asset, Balance, PositionCostBasis, TradeOrder
from app.services.market_price_service import (
    MarketPriceError,
    get_market_price,
)


ZERO = Decimal("0")
QUANTUM = Decimal("0.000000000000000001")


def _decimal(value):
    return Decimal(str(value if value is not None else "0"))


def _quantize(value):
    return value.quantize(QUANTUM)


def get_or_create_position(wallet_id, asset_id):
    """Get a cost-basis record, initializing legacy holdings as unknown-cost."""
    position = db.session.execute(
        select(PositionCostBasis)
        .where(
            PositionCostBasis.wallet_id == wallet_id,
            PositionCostBasis.asset_id == asset_id,
        )
        .with_for_update()
    ).scalar_one_or_none()

    if position is not None:
        return position

    # Read the balance BEFORE the trade modifies it. Existing holdings have
    # unknown historical cost; do not invent a purchase price for them.
    balance = db.session.execute(
        select(Balance)
        .where(
            Balance.wallet_id == wallet_id,
            Balance.asset_id == asset_id,
        )
        .with_for_update()
    ).scalar_one_or_none()

    existing_quantity = ZERO
    if balance is not None:
        existing_quantity = (
            _decimal(balance.available) + _decimal(balance.reserved)
        )

    position = PositionCostBasis(
        wallet_id=wallet_id,
        asset_id=asset_id,
        known_quantity=ZERO,
        known_cost_basis_usd=ZERO,
        unknown_quantity=_quantize(existing_quantity),
    )
    db.session.add(position)
    db.session.flush()

    return position


def record_buy(
    wallet_id,
    asset_id,
    quantity,
    gross_usd,
    fee_usd,
):
    """Record a buy at its USD cost, including the buy fee."""
    position = get_or_create_position(wallet_id, asset_id)

    with localcontext() as context:
        context.prec = 60

        position.known_quantity = _quantize(
            _decimal(position.known_quantity) + quantity
        )
        position.known_cost_basis_usd = _quantize(
            _decimal(position.known_cost_basis_usd)
            + gross_usd
            + fee_usd
        )

    return position


def record_sell(
    wallet_id,
    asset_id,
    quantity,
    gross_usd,
    fee_usd,
):
    """
    Dispose of unknown-cost units first, then calculate P&L on known-cost units.

    Returns (realized_pnl_usd, is_complete). The P&L value is the known-basis
    portion only. It is zero if no known-cost units were sold; the completeness
    flag distinguishes that partial result from a complete calculation.
    """
    position = get_or_create_position(wallet_id, asset_id)

    with localcontext() as context:
        context.prec = 60

        known_quantity = _decimal(position.known_quantity)
        known_cost = _decimal(position.known_cost_basis_usd)
        unknown_quantity = _decimal(position.unknown_quantity)

        if known_quantity < ZERO or known_cost < ZERO or unknown_quantity < ZERO:
            raise ValueError("Cost-basis position contains a negative value.")

        unknown_sold = min(unknown_quantity, quantity)
        known_sold = quantity - unknown_sold

        if known_sold > known_quantity:
            raise ValueError(
                "Cost-basis quantity is inconsistent with the position."
            )

        if known_sold > ZERO and known_quantity <= ZERO:
            raise ValueError(
                "Cost-basis quantity is inconsistent with the position."
            )

        position.unknown_quantity = _quantize(
            unknown_quantity - unknown_sold
        )

        # Store the known-basis P&L portion as zero if the entire sale has
        # unknown cost basis. realized_pnl_complete conveys whether it is final.
        realized_pnl = ZERO

        if known_sold > ZERO:
            average_cost = known_cost / known_quantity
            allocated_cost = average_cost * known_sold

            # Allocate net sale proceeds proportionally to the known-cost units.
            known_fraction = known_sold / quantity
            known_net_proceeds = (
                (gross_usd - fee_usd) * known_fraction
            )

            realized_pnl = _quantize(
                known_net_proceeds - allocated_cost
            )

            position.known_quantity = _quantize(
                known_quantity - known_sold
            )
            position.known_cost_basis_usd = _quantize(
                max(ZERO, known_cost - allocated_cost)
            )

            if position.known_quantity == ZERO:
                position.known_cost_basis_usd = ZERO

        return realized_pnl, unknown_sold == ZERO


def get_wallet_pnl(wallet_id):
    """Build a wallet P&L summary in USD without inventing missing prices."""
    assets = db.session.execute(
        select(Asset)
        .where(
            Asset.symbol.in_(["BTC", "ETH"]),
            Asset.is_active.is_(True),
        )
        .order_by(Asset.symbol)
    ).scalars().all()

    positions = db.session.execute(
        select(PositionCostBasis, Asset.symbol)
        .join(Asset, Asset.id == PositionCostBasis.asset_id)
        .where(PositionCostBasis.wallet_id == wallet_id)
        .order_by(Asset.symbol)
    ).all()

    position_by_symbol = {
        symbol: position for position, symbol in positions
    }

    # Read live wallet balances as a fallback for legacy/newly funded holdings
    # that do not yet have a cost-basis row. Their historical basis is unknown.
    balance_rows = db.session.execute(
        select(Asset.symbol, Balance.available, Balance.reserved)
        .join(Asset, Asset.id == Balance.asset_id)
        .where(
            Balance.wallet_id == wallet_id,
            Asset.symbol.in_(["BTC", "ETH"]),
        )
    ).all()
    balance_by_symbol = {
        symbol: _decimal(available) + _decimal(reserved)
        for symbol, available, reserved in balance_rows
    }

    rows = []
    unrealized_total = ZERO
    unrealized_complete = True

    for asset in assets:
        position = position_by_symbol.get(asset.symbol)

        if position is None:
            known_quantity = ZERO
            known_cost = ZERO
            unknown_quantity = balance_by_symbol.get(asset.symbol, ZERO)
        else:
            known_quantity = _decimal(position.known_quantity)
            known_cost = _decimal(position.known_cost_basis_usd)
            unknown_quantity = _decimal(position.unknown_quantity)

        total_quantity = known_quantity + unknown_quantity
        market_price = None
        known_market_value = None
        unknown_market_value = None
        market_value = None
        unrealized_pnl = None

        # Value all units at the indicative market price, even when historical
        # cost basis is unknown. Market value is not the same as P&L.
        if total_quantity > ZERO:
            try:
                market_price = get_market_price(asset.symbol, "USD")
                market_value = _quantize(total_quantity * market_price)
                if known_quantity > ZERO:
                    known_market_value = _quantize(
                        known_quantity * market_price
                    )
                    unknown_market_value = _quantize(
                        unknown_quantity * market_price
                    )
                    unrealized_pnl = _quantize(
                        known_market_value - known_cost
                    )
                    unrealized_total += unrealized_pnl
                elif unknown_quantity > ZERO:
                    unknown_market_value = _quantize(
                        unknown_quantity * market_price
                    )
            except MarketPriceError:
                unrealized_complete = False

        if unknown_quantity > ZERO:
            # Unknown historical cost means P&L cannot be fully determined.
            unrealized_complete = False

        if total_quantity > ZERO and market_price is None:
            unrealized_complete = False

        rows.append({
            "asset": asset.symbol,
            "known_quantity": str(known_quantity),
            "unknown_quantity": str(unknown_quantity),
            "total_quantity": str(total_quantity),
            "known_cost_basis_usd": str(known_cost),
            "market_price_usd": (
                str(market_price) if market_price is not None else None
            ),
            "known_market_value_usd": (
                str(known_market_value)
                if known_market_value is not None
                else None
            ),
            "unknown_market_value_usd": (
                str(unknown_market_value)
                if unknown_market_value is not None
                else None
            ),
            "market_value_usd": (
                str(market_value) if market_value is not None else None
            ),
            "unrealized_pnl_usd": (
                str(unrealized_pnl)
                if unrealized_pnl is not None
                else None
            ),
            "unrealized_pnl_complete": (
                unknown_quantity == ZERO
                and (
                    total_quantity == ZERO
                    or market_price is not None
                )
            ),
        })

    realized_value = db.session.execute(
        select(func.coalesce(func.sum(TradeOrder.realized_pnl_usd), 0))
        .where(
            TradeOrder.wallet_id == wallet_id,
            TradeOrder.side == "SELL",
        )
    ).scalar_one()

    incomplete_realized_count = db.session.execute(
        select(func.count(TradeOrder.id))
        .where(
            TradeOrder.wallet_id == wallet_id,
            TradeOrder.side == "SELL",
            TradeOrder.realized_pnl_complete.is_(False),
        )
    ).scalar_one()

    realized_complete = incomplete_realized_count == 0

    result = {
        "wallet_id": wallet_id,
        "currency": "USD",
        "accounting_method": "weighted_average_known_cost_unknown_first",
        "realized_pnl_usd": str(_quantize(_decimal(realized_value))),
        "realized_pnl_complete": realized_complete,
        "unrealized_pnl_usd": str(_quantize(unrealized_total)),
        "unrealized_pnl_complete": unrealized_complete,
        "positions": rows,
        "notes": [
            "P&L is based on simulated orders and indicative market prices.",
            "Market value includes known- and unknown-cost holdings when prices are available.",
            "Unknown-cost holdings are excluded from known-basis P&L.",
            "Realized P&L is incomplete when a sale includes unknown-cost units.",
        ],
    }

    # Avoid presenting a combined total when any required component is partial.
    result["total_pnl_usd"] = (
        str(_quantize(_decimal(realized_value) + unrealized_total))
        if realized_complete and unrealized_complete
        else None
    )

    return result