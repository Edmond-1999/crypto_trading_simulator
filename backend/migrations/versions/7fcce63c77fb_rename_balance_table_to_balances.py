
"""Rename balance table to balances

Revision ID: 7fcce63c77fb
Revises: 1ac9448e9f82
"""

from alembic import op

revision = "7fcce63c77fb"
down_revision = "1ac9448e9f82"
branch_labels = None
depends_on = None


def upgrade():
    op.rename_table("balance", "balances")


def downgrade():
    op.rename_table("balances", "balance")
