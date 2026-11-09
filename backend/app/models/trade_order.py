from datetime import datetime, timezone

from app.extensions import db


class TradeOrder(db.Model):
    __tablename__ = "trade_orders"

    id = db.Column(db.Integer, primary_key=True)

    wallet_id = db.Column(
        db.Integer,
        db.ForeignKey("wallets.id"),
        nullable=False,
        index=True,
    )

    base_asset_id = db.Column(
        db.Integer,
        db.ForeignKey("assets.id"),
        nullable=False,
    )

    quote_asset_id = db.Column(
        db.Integer,
        db.ForeignKey("assets.id"),
        nullable=False,
    )

    side = db.Column(db.String(4), nullable=False)

    order_type = db.Column(
        db.String(10),
        nullable=False,
        default="market",
    )

    quantity = db.Column(db.Numeric(36, 18), nullable=False)
    price = db.Column(db.Numeric(36, 18), nullable=False)
    quote_amount = db.Column(db.Numeric(36, 18), nullable=False)
    fee = db.Column(db.Numeric(36, 18), nullable=False)

    fee_rate = db.Column(db.Numeric(8, 6), nullable=False)

    price_source = db.Column(
        db.String(40),
        nullable=False,
        default="public_market_api",
    )

    status = db.Column(
        db.String(20),
        nullable=False,
        default="filled",
    )

    # USD profit/loss for the known-cost portion of a sell.
    # NULL means no reliable realized figure is available.
    realized_pnl_usd = db.Column(
        db.Numeric(36, 18),
        nullable=True,
    )

    # False means some or all of the sell's cost basis is unknown.
    realized_pnl_complete = db.Column(
        db.Boolean,
        nullable=False,
        default=True,
    )

    created_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )