from datetime import timezone, datetime

from app.extensions import db


class Balance(db.Model):
    __tablename__ = "balances"

    id = db.Column(db.Integer, primary_key=True)

    wallet_id = db.Column(
        db.Integer,
        db.ForeignKey("wallets.id", ondelete="CASCADE"),
        nullable=False,
    )

    asset_id = db.Column(
        db.Integer,
        db.ForeignKey("assets.id"),
        nullable=False,
    )

    available = db.Column(
        db.Numeric(36, 18),
        nullable=False,
        default=0,
    )

    reserved = db.Column(
        db.Numeric(36, 18),
        nullable=False,
        default=0,
    )

    updated_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda : datetime.now(timezone.utc),
        onupdate=lambda : datetime.now(timezone.utc),
    )

    wallet = db.relationship("Wallet", backref="balances")
    asset = db.relationship("Asset")

    __table_args__ = (
        db.UniqueConstraint(
            "wallet_id",
            "asset_id",
            name="uq_balance_wallet_asset",
        ),
        db.CheckConstraint(
            "available >= 0",
            name="ck_balance_available_nonnegative",
        ),
        db.CheckConstraint(
            "reserved >= 0",
            name="ck_balance_reserved_nonnegative",
        ),
    )