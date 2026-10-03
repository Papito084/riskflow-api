import uuid
from datetime import UTC, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from src.domain.enums import TradeDirection, TradeStatus


class TradeCreate(BaseModel):
    account_id: uuid.UUID
    symbol: str = Field(
        ..., min_length=2, max_length=20, description="Financial asset symbol e.g. XAUUSD"
    )
    direction: TradeDirection = Field(..., description="Trade direction: BUY or SELL")
    entry_price: Decimal = Field(..., gt=0, description="Price at which trade entered the market")
    lot_size: Decimal = Field(..., gt=0, description="Volume/lot size traded")
    exit_price: Decimal | None = Field(
        None, gt=0, description="Price at which trade exited (if closed)"
    )
    pnl: Decimal | None = Field(None, description="Profit or loss realized")
    opened_at: datetime | None = Field(default_factory=lambda: datetime.now(UTC))
    closed_at: datetime | None = Field(None, description="Closing timestamp")
    status: TradeStatus = Field(default=TradeStatus.OPEN)

    @field_validator("symbol")
    @classmethod
    def normalize_symbol(cls, v: str) -> str:
        return v.strip().upper()

    @model_validator(mode="after")
    def validate_closed_trade_requirements(self) -> "TradeCreate":
        if self.status == TradeStatus.CLOSED:
            if self.exit_price is None:
                raise ValueError("exit_price is required when trade status is CLOSED")
            if self.closed_at is None:
                self.closed_at = datetime.now(UTC)
        return self


class TradeCloseRequest(BaseModel):
    exit_price: Decimal = Field(..., gt=0, description="Exit price to close the trade")
    pnl: Decimal | None = Field(
        None, description="Realized PnL. If omitted, can be calculated or provided"
    )
    closed_at: datetime | None = Field(default_factory=lambda: datetime.now(UTC))


class TradeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    account_id: uuid.UUID
    symbol: str
    direction: TradeDirection
    entry_price: Decimal
    exit_price: Decimal | None
    lot_size: Decimal
    pnl: Decimal | None
    opened_at: datetime
    closed_at: datetime | None
    status: TradeStatus


class TradeEventNotification(BaseModel):
    event_type: str  # e.g., "TRADE_CREATED", "TRADE_CLOSED"
    account_id: uuid.UUID
    trade: TradeResponse
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
