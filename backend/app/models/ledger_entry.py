from datetime import timezone, datetime

from app.extensions import db


class LedgerEntry(db.Model):
    __tablename__ = "ledger_entries"

    id = db.Column(db.Integer, primary_key=True)

    wallet_id = db.Column(
        db.Integer,
        db.ForeignKey("wallets.id"),
        nullable=False,
        index=True,
    )

    asset_id = db.Column(
        db.Integer,
        db.ForeignKey("assets.id"),
        nullable=False,
    )

    entry_type = db.Column(db.String(30), nullable=False)

    amount = db.Column(db.Numeric(36, 18), nullable=False)

    reference = db.Column(db.String(100), nullable=False, index=True)

    created_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc)
    )