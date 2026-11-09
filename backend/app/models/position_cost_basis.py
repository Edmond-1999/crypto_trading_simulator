from datetime import datetime, timezone

from app.extensions import db


class PositionCostBasis(db.Model):
    __tablename__ = "position_cost_basis"

    id = db.Column(db.Integer, primary_key=True)

    wallet_id = db.Column(
        db.Integer,
        db.ForeignKey("wallets.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    asset_id = db.Column(
        db.Integer,
        db.ForeignKey("assets.id"),
        nullable=False,
        index=True,
    )

    # Quantity whose acquisition cost is known.
    known_quantity = db.Column(
        db.Numeric(36, 18),
        nullable=False,
        default=0,
    )

    # Total acquisition cost of known_quantity, denominated in USD.
    # Buy fees are included.
    known_cost_basis_usd = db.Column(
        db.Numeric(36, 18),
        nullable=False,
        default=0,
    )

    # Existing or otherwise untracked holdings with unknown acquisition cost.
    unknown_quantity = db.Column(
        db.Numeric(36, 18),
        nullable=False,
        default=0,
    )

    updated_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    wallet = db.relationship("Wallet")
    asset = db.relationship("Asset")

    __table_args__ = (
        db.UniqueConstraint(
            "wallet_id",
            "asset_id",
            name="uq_position_cost_basis_wallet_asset",
        ),
        db.CheckConstraint(
            "known_quantity >= 0",
            name="ck_position_cost_basis_known_quantity_nonnegative",
        ),
        db.CheckConstraint(
            "known_cost_basis_usd >= 0",
            name="ck_position_cost_basis_cost_nonnegative",
        ),
        db.CheckConstraint(
            "unknown_quantity >= 0",
            name="ck_position_cost_basis_unknown_quantity_nonnegative",
        ),
    )