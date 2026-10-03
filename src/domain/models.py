import uuid
from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Index,
    Numeric,
    String,
    Uuid,
    func,
)
from sqlalchemy import (
    Enum as SAEnum,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.database import Base
from src.domain.enums import BrokerType, Currency, TradeDirection, TradeStatus


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        index=True,
        nullable=False,
    )
    hashed_password: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    accounts: Mapped[list["TradingAccount"]] = relationship(
        "TradingAccount",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class TradingAccount(Base):
    __tablename__ = "trading_accounts"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    broker_type: Mapped[BrokerType] = mapped_column(
        SAEnum(BrokerType, native_enum=False, length=20),
        nullable=False,
        default=BrokerType.PERSONAL,
    )
    initial_balance: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        nullable=False,
    )
    current_balance: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        nullable=False,
    )
    currency: Mapped[Currency] = mapped_column(
        SAEnum(Currency, native_enum=False, length=10),
        nullable=False,
        default=Currency.USD,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    user: Mapped["User"] = relationship(
        "User",
        back_populates="accounts",
    )
    trades: Mapped[list["Trade"]] = relationship(
        "Trade",
        back_populates="account",
        cascade="all, delete-orphan",
        order_by="Trade.opened_at.asc()",
    )


class Trade(Base):
    __tablename__ = "trades"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    account_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("trading_accounts.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    symbol: Mapped[str] = mapped_column(
        String(20),
        index=True,
        nullable=False,
    )
    direction: Mapped[TradeDirection] = mapped_column(
        SAEnum(TradeDirection, native_enum=False, length=10),
        nullable=False,
    )
    entry_price: Mapped[Decimal] = mapped_column(
        Numeric(18, 5),
        nullable=False,
    )
    exit_price: Mapped[Decimal | None] = mapped_column(
        Numeric(18, 5),
        nullable=True,
    )
    lot_size: Mapped[Decimal] = mapped_column(
        Numeric(12, 4),
        nullable=False,
    )
    pnl: Mapped[Decimal | None] = mapped_column(
        Numeric(18, 2),
        nullable=True,
    )
    opened_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )
    closed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    status: Mapped[TradeStatus] = mapped_column(
        SAEnum(TradeStatus, native_enum=False, length=10),
        nullable=False,
        default=TradeStatus.OPEN,
        index=True,
    )

    # Relationships
    account: Mapped["TradingAccount"] = relationship(
        "TradingAccount",
        back_populates="trades",
    )

    # Indexes
    __table_args__ = (
        Index("ix_trades_account_opened_at", "account_id", "opened_at"),
        Index("ix_trades_account_status", "account_id", "status"),
    )
