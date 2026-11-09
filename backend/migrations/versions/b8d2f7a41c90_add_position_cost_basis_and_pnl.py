"""Add position cost basis and realized P&L.

Revision ID: b8d2f7a41c90
Revises: 0a11cbdac7e5
"""

from alembic import op
import sqlalchemy as sa


revision = "b8d2f7a41c90"
down_revision = "0a11cbdac7e5"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "position_cost_basis",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "wallet_id",
            sa.Integer(),
            sa.ForeignKey("wallets.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "asset_id",
            sa.Integer(),
            sa.ForeignKey("assets.id"),
            nullable=False,
        ),
        sa.Column(
            "known_quantity",
            sa.Numeric(36, 18),
            nullable=False,
            server_default="0",
        ),
        sa.Column(
            "known_cost_basis_usd",
            sa.Numeric(36, 18),
            nullable=False,
            server_default="0",
        ),
        sa.Column(
            "unknown_quantity",
            sa.Numeric(36, 18),
            nullable=False,
            server_default="0",
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.UniqueConstraint(
            "wallet_id",
            "asset_id",
            name="uq_position_cost_basis_wallet_asset",
        ),
        sa.CheckConstraint(
            "known_quantity >= 0",
            name="ck_position_cost_basis_known_quantity_nonnegative",
        ),
        sa.CheckConstraint(
            "known_cost_basis_usd >= 0",
            name="ck_position_cost_basis_cost_nonnegative",
        ),
        sa.CheckConstraint(
            "unknown_quantity >= 0",
            name="ck_position_cost_basis_unknown_quantity_nonnegative",
        ),
    )

    op.create_index(
        "ix_position_cost_basis_wallet_id",
        "position_cost_basis",
        ["wallet_id"],
    )
    op.create_index(
        "ix_position_cost_basis_asset_id",
        "position_cost_basis",
        ["asset_id"],
    )

    # Every existing BTC/ETH balance starts as unknown-cost inventory.
    # Include both available and reserved quantities.
    connection = op.get_bind()

    balances = sa.table(
        "balances",
        sa.column("wallet_id", sa.Integer()),
        sa.column("asset_id", sa.Integer()),
        sa.column("available", sa.Numeric(36, 18)),
        sa.column("reserved", sa.Numeric(36, 18)),
    )

    assets = sa.table(
        "assets",
        sa.column("id", sa.Integer()),
        sa.column("symbol", sa.String(20)),
    )

    rows = connection.execute(
        sa.select(
            balances.c.wallet_id,
            balances.c.asset_id,
            balances.c.available,
            balances.c.reserved,
        )
        .select_from(
            balances.join(
                assets,
                balances.c.asset_id == assets.c.id,
            )
        )
        .where(assets.c.symbol.in_(["BTC", "ETH"]))
    ).mappings()

    for row in rows:
        unknown_quantity = (
            (row["available"] or 0) + (row["reserved"] or 0)
        )

        connection.execute(
            sa.text(
                """
                INSERT INTO position_cost_basis (
                    wallet_id,
                    asset_id,
                    known_quantity,
                    known_cost_basis_usd,
                    unknown_quantity,
                    updated_at
                )
                VALUES (
                    :wallet_id,
                    :asset_id,
                    0,
                    0,
                    :unknown_quantity,
                    CURRENT_TIMESTAMP
                )
                """
            ),
            {
                "wallet_id": row["wallet_id"],
                "asset_id": row["asset_id"],
                "unknown_quantity": unknown_quantity,
            },
        )

    # Old buys are not realized sales. Historical sells remain explicitly
    # incomplete because their cost basis cannot be reconstructed safely.
    op.add_column(
        "trade_orders",
        sa.Column(
            "realized_pnl_usd",
            sa.Numeric(36, 18),
            nullable=True,
        ),
    )
    op.add_column(
        "trade_orders",
        sa.Column(
            "realized_pnl_complete",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )

    connection.execute(
        sa.text(
            """
            UPDATE trade_orders
            SET realized_pnl_usd = 0,
                realized_pnl_complete = TRUE
            WHERE UPPER(side) = 'BUY'
            """
        )
    )


def downgrade():
    op.drop_column("trade_orders", "realized_pnl_complete")
    op.drop_column("trade_orders", "realized_pnl_usd")

    op.drop_index(
        "ix_position_cost_basis_asset_id",
        table_name="position_cost_basis",
    )
    op.drop_index(
        "ix_position_cost_basis_wallet_id",
        table_name="position_cost_basis",
    )
    op.drop_table("position_cost_basis")