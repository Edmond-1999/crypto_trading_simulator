from datetime import timezone, datetime

from app.extensions import db


class Wallet(db.Model):
    __tablename__ = "wallets"

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    name = db.Column(db.String(100), nullable=False)

    base_currency = db.Column(
        db.String(10),
        nullable=False,
        default="USD",
    )

    created_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc)
    )

    user = db.relationship("User", backref="wallets")

