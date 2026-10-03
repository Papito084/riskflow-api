import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class RiskMetricsResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    account_id: uuid.UUID
    total_trades: int
    closed_trades: int
    open_trades: int
    winning_trades: int
    losing_trades: int
    break_even_trades: int

    # Percentage metrics
    win_rate_pct: Decimal
    loss_rate_pct: Decimal

    # Financial totals
    gross_profit: Decimal
    gross_loss: Decimal
    net_profit: Decimal

    # Ratios and mathematical metrics
    profit_factor: Decimal | None
    max_drawdown_amount: Decimal
    max_drawdown_pct: Decimal
    average_win: Decimal
    average_loss: Decimal
    risk_reward_ratio: Decimal | None
    expectancy: Decimal

    # Meta
    cached: bool = False
    calculated_at: datetime
