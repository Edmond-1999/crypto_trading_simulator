from app.extensions import db


class Asset(db.Model):
    __tablename__ = "assets"

    id = db.Column(db.Integer, primary_key=True)

    symbol = db.Column(
        db.String(20),
        nullable=False,
        unique=True,
        index=True,
    )

    name = db.Column(db.String(20), nullable=False)

    asset_type = db.Column(
        db.String(20),
        nullable=False,
        default="crypto",
    )

    is_active = db.Column(db.Boolean, nullable=False, default=True)