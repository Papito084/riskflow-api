import uuid
from datetime import UTC, datetime
from decimal import ROUND_HALF_UP, Decimal

import redis.asyncio as aioredis

from src.core.config import settings
from src.core.redis import RedisCacheService
from src.domain.enums import TradeStatus
from src.domain.models import Trade
from src.schemas.analytics import RiskMetricsResponse

TWO_PLACES = Decimal("0.01")
FOUR_PLACES = Decimal("0.0001")


def round_decimal(val: Decimal, places: Decimal = TWO_PLACES) -> Decimal:
    return val.quantize(places, rounding=ROUND_HALF_UP)


class RiskAnalyticsEngine:
    """Pure mathematical engine for trading performance and risk calculations."""

    @staticmethod
    def calculate_metrics(
        account_id: uuid.UUID,
        initial_balance: Decimal,
        trades: list[Trade],
    ) -> RiskMetricsResponse:
        total_trades = len(trades)
        closed_trades = [t for t in trades if t.status == TradeStatus.CLOSED and t.pnl is not None]
        open_trades = [t for t in trades if t.status == TradeStatus.OPEN]

        n_closed = len(closed_trades)
        n_open = len(open_trades)

        if n_closed == 0:
            return RiskMetricsResponse(
                account_id=account_id,
                total_trades=total_trades,
                closed_trades=0,
                open_trades=n_open,
                winning_trades=0,
                losing_trades=0,
                break_even_trades=0,
                win_rate_pct=Decimal("0.00"),
                loss_rate_pct=Decimal("0.00"),
                gross_profit=Decimal("0.00"),
                gross_loss=Decimal("0.00"),
                net_profit=Decimal("0.00"),
                profit_factor=None,
                max_drawdown_amount=Decimal("0.00"),
                max_drawdown_pct=Decimal("0.00"),
                average_win=Decimal("0.00"),
                average_loss=Decimal("0.00"),
                risk_reward_ratio=None,
                expectancy=Decimal("0.00"),
                cached=False,
                calculated_at=datetime.now(UTC),
            )

        winning_trades: list[Trade] = []
        losing_trades: list[Trade] = []
        break_even_trades: list[Trade] = []

        gross_profit = Decimal("0.00")
        gross_loss = Decimal("0.00")

        # Chronological sort for drawdown tracking
        sorted_trades = sorted(closed_trades, key=lambda t: t.opened_at)

        current_equity = initial_balance
        peak_equity = initial_balance
        max_dd_amount = Decimal("0.00")
        max_dd_pct = Decimal("0.00")

        for trade in sorted_trades:
            pnl = Decimal(str(trade.pnl)) if trade.pnl is not None else Decimal("0.00")

            if pnl > Decimal("0"):
                winning_trades.append(trade)
                gross_profit += pnl
            elif pnl < Decimal("0"):
                losing_trades.append(trade)
                gross_loss += abs(pnl)
            else:
                break_even_trades.append(trade)

            # Drawdown calculations on cumulative equity
            current_equity += pnl
            if current_equity > peak_equity:
                peak_equity = current_equity
            else:
                dd_amount = peak_equity - current_equity
                if dd_amount > max_dd_amount:
                    max_dd_amount = dd_amount
                if peak_equity > Decimal("0"):
                    dd_pct = (dd_amount / peak_equity) * Decimal("100")
                    if dd_pct > max_dd_pct:
                        max_dd_pct = dd_pct

        n_wins = len(winning_trades)
        n_losses = len(losing_trades)
        n_be = len(break_even_trades)

        n_closed_dec = Decimal(str(n_closed))
        win_rate_pct = round_decimal((Decimal(str(n_wins)) / n_closed_dec) * Decimal("100"))
        loss_rate_pct = round_decimal((Decimal(str(n_losses)) / n_closed_dec) * Decimal("100"))

        net_profit = round_decimal(gross_profit - gross_loss)
        gross_profit = round_decimal(gross_profit)
        gross_loss = round_decimal(gross_loss)

        # Profit Factor: Gross Profits / Gross Losses
        if gross_loss > Decimal("0"):
            profit_factor: Decimal | None = round_decimal(
                gross_profit / gross_loss, places=FOUR_PLACES
            )
        else:
            profit_factor = None  # Undefined/Infinity when no losses exist

        # Average win and loss
        average_win = (
            round_decimal(gross_profit / Decimal(str(n_wins))) if n_wins > 0 else Decimal("0.00")
        )
        average_loss = (
            round_decimal(gross_loss / Decimal(str(n_losses))) if n_losses > 0 else Decimal("0.00")
        )

        # Risk/Reward Ratio: Average Win / Average Loss
        if average_loss > Decimal("0"):
            risk_reward_ratio: Decimal | None = round_decimal(
                average_win / average_loss, places=FOUR_PLACES
            )
        else:
            risk_reward_ratio = None

        # Mathematical Expectancy: (Win Rate * Avg Win) - (Loss Rate * Avg Loss)
        win_rate_dec = Decimal(str(n_wins)) / n_closed_dec
        loss_rate_dec = Decimal(str(n_losses)) / n_closed_dec
        expectancy = round_decimal((win_rate_dec * average_win) - (loss_rate_dec * average_loss))

        return RiskMetricsResponse(
            account_id=account_id,
            total_trades=total_trades,
            closed_trades=n_closed,
            open_trades=n_open,
            winning_trades=n_wins,
            losing_trades=n_losses,
            break_even_trades=n_be,
            win_rate_pct=win_rate_pct,
            loss_rate_pct=loss_rate_pct,
            gross_profit=gross_profit,
            gross_loss=gross_loss,
            net_profit=net_profit,
            profit_factor=profit_factor,
            max_drawdown_amount=round_decimal(max_dd_amount),
            max_drawdown_pct=round_decimal(max_dd_pct),
            average_win=average_win,
            average_loss=average_loss,
            risk_reward_ratio=risk_reward_ratio,
            expectancy=expectancy,
            cached=False,
            calculated_at=datetime.now(UTC),
        )


class AnalyticsService:
    """Service wrapping calculation with Redis caching."""

    def __init__(self, redis: aioredis.Redis | None = None) -> None:
        self.redis = redis
        self.cache_service = RedisCacheService(redis) if redis is not None else None

    @staticmethod
    def get_cache_key(account_id: uuid.UUID) -> str:
        return f"analytics:account:{account_id}"

    async def get_account_metrics(
        self,
        account_id: uuid.UUID,
        initial_balance: Decimal,
        trades: list[Trade],
    ) -> RiskMetricsResponse:
        cache_key = self.get_cache_key(account_id)

        # Check Redis Cache
        if self.cache_service:
            cached_data = await self.cache_service.get_json(cache_key)
            if cached_data:
                cached_data["cached"] = True
                return RiskMetricsResponse.model_validate(cached_data)

        # Compute pure metrics
        metrics = RiskAnalyticsEngine.calculate_metrics(
            account_id=account_id,
            initial_balance=initial_balance,
            trades=trades,
        )

        # Store in Redis Cache
        if self.cache_service:
            await self.cache_service.set_json(
                cache_key,
                metrics.model_dump(mode="json"),
                ttl=settings.METRICS_CACHE_TTL_SECONDS,
            )

        return metrics

    async def invalidate_metrics_cache(self, account_id: uuid.UUID) -> None:
        if self.cache_service:
            await self.cache_service.delete(self.get_cache_key(account_id))
