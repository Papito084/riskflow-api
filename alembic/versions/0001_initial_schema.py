"""Initial schema for users, trading accounts, and trades

Revision ID: 0001_initial_schema
Revises:
Create Date: 2026-10-03 12:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0001_initial_schema"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 1. Users table
    op.create_table(
        "users",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("hashed_password", sa.String(length=255), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=True)

    # 2. Trading accounts table
    op.create_table(
        "trading_accounts",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("broker_type", sa.String(length=20), nullable=False),
        sa.Column("initial_balance", sa.Numeric(precision=18, scale=2), nullable=False),
        sa.Column("current_balance", sa.Numeric(precision=18, scale=2), nullable=False),
        sa.Column("currency", sa.String(length=10), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_trading_accounts_user_id"), "trading_accounts", ["user_id"], unique=False
    )

    # 3. Trades table
    op.create_table(
        "trades",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("account_id", sa.Uuid(), nullable=False),
        sa.Column("symbol", sa.String(length=20), nullable=False),
        sa.Column("direction", sa.String(length=10), nullable=False),
        sa.Column("entry_price", sa.Numeric(precision=18, scale=5), nullable=False),
        sa.Column("exit_price", sa.Numeric(precision=18, scale=5), nullable=True),
        sa.Column("lot_size", sa.Numeric(precision=12, scale=4), nullable=False),
        sa.Column("pnl", sa.Numeric(precision=18, scale=2), nullable=True),
        sa.Column("opened_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("closed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.String(length=10), nullable=False),
        sa.ForeignKeyConstraint(["account_id"], ["trading_accounts.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_trades_account_id"), "trades", ["account_id"], unique=False)
    op.create_index(op.f("ix_trades_symbol"), "trades", ["symbol"], unique=False)
    op.create_index(op.f("ix_trades_status"), "trades", ["status"], unique=False)
    op.create_index(
        "ix_trades_account_opened_at", "trades", ["account_id", "opened_at"], unique=False
    )
    op.create_index("ix_trades_account_status", "trades", ["account_id", "status"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_trades_account_status", table_name="trades")
    op.drop_index("ix_trades_account_opened_at", table_name="trades")
    op.drop_index(op.f("ix_trades_status"), table_name="trades")
    op.drop_index(op.f("ix_trades_symbol"), table_name="trades")
    op.drop_index(op.f("ix_trades_account_id"), table_name="trades")
    op.drop_table("trades")

    op.drop_index(op.f("ix_trading_accounts_user_id"), table_name="trading_accounts")
    op.drop_table("trading_accounts")

    op.drop_index(op.f("ix_users_email"), table_name="users")
    op.drop_table("users")
