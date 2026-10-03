import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from src.domain.enums import BrokerType, Currency


class TradingAccountCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=100, description="Account name or label")
    broker_type: BrokerType = Field(default=BrokerType.PERSONAL)
    initial_balance: Decimal = Field(..., gt=0, description="Starting account balance")
    currency: Currency = Field(default=Currency.USD)


class TradingAccountUpdate(BaseModel):
    name: str | None = Field(None, min_length=2, max_length=100)
    broker_type: BrokerType | None = None


class TradingAccountResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    name: str
    broker_type: BrokerType
    initial_balance: Decimal
    current_balance: Decimal
    currency: Currency
    created_at: datetime
