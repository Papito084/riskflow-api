import uuid
from datetime import UTC, datetime

import redis.asyncio as aioredis
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.redis import RedisCacheService
from src.domain.enums import TradeDirection, TradeStatus
from src.domain.exceptions import (
    AccountNotFoundException,
    InvalidTradeStateException,
    TradeNotFoundException,
    UnauthorizedAccessException,
)
from src.domain.models import Trade
from src.repositories.account_repository import AccountRepository
from src.repositories.trade_repository import TradeRepository
from src.schemas.trade import (
    TradeCloseRequest,
    TradeCreate,
    TradeEventNotification,
    TradeResponse,
)
from src.services.analytics import AnalyticsService
from src.services.websocket_manager import ws_manager


class TradeService:
    def __init__(self, session: AsyncSession, redis: aioredis.Redis | None = None) -> None:
        self.session = session
        self.redis = redis
        self.trade_repo = TradeRepository(session)
        self.account_repo = AccountRepository(session)
        self.analytics_service = AnalyticsService(redis)
        self.redis_cache = RedisCacheService(redis) if redis is not None else None

    async def create_trade(self, user_id: uuid.UUID, data: TradeCreate) -> TradeResponse:
        account = await self.account_repo.get_by_id(data.account_id)
        if not account:
            raise AccountNotFoundException(f"Trading account '{data.account_id}' not found.")
        if account.user_id != user_id:
            raise UnauthorizedAccessException(
                "You are not authorized to create trades for this account."
            )

        pnl = data.pnl
        if data.status == TradeStatus.CLOSED and pnl is None and data.exit_price is not None:
            # Automatic PnL calculation if omitted
            if data.direction == TradeDirection.BUY:
                pnl = (data.exit_price - data.entry_price) * data.lot_size
            else:
                pnl = (data.entry_price - data.exit_price) * data.lot_size

        new_trade = Trade(
            account_id=data.account_id,
            symbol=data.symbol,
            direction=data.direction,
            entry_price=data.entry_price,
            exit_price=data.exit_price,
            lot_size=data.lot_size,
            pnl=pnl,
            opened_at=data.opened_at or datetime.now(UTC),
            closed_at=data.closed_at,
            status=data.status,
        )

        created = await self.trade_repo.create(new_trade)

        # Update account balance if closed
        if created.status == TradeStatus.CLOSED and created.pnl is not None:
            account.current_balance += created.pnl
            await self.account_repo.update(account)

        # Invalidate Redis Metrics Cache
        await self.analytics_service.invalidate_metrics_cache(account.id)

        response_dto = TradeResponse.model_validate(created)

        # Propagate Real-Time Event via Redis PubSub & WebSocket
        event = TradeEventNotification(
            event_type="TRADE_CREATED",
            account_id=account.id,
            trade=response_dto,
            timestamp=datetime.now(UTC),
        )
        event_dict = event.model_dump(mode="json")

        if self.redis_cache:
            await self.redis_cache.publish(f"account:{account.id}:events", event_dict)
        # Direct local socket broadcast as well
        await ws_manager.broadcast_to_account(account.id, event_dict)

        return response_dto

    async def close_trade(
        self,
        trade_id: uuid.UUID,
        user_id: uuid.UUID,
        data: TradeCloseRequest,
    ) -> TradeResponse:
        trade = await self.trade_repo.get_by_id(trade_id)
        if not trade:
            raise TradeNotFoundException(f"Trade '{trade_id}' not found.")

        account = await self.account_repo.get_by_id(trade.account_id)
        if not account or account.user_id != user_id:
            raise UnauthorizedAccessException("You are not authorized to modify this trade.")

        if trade.status == TradeStatus.CLOSED:
            raise InvalidTradeStateException("Trade is already closed.")

        trade.status = TradeStatus.CLOSED
        trade.exit_price = data.exit_price
        trade.closed_at = data.closed_at or datetime.now(UTC)

        # Calculate realized PnL
        if data.pnl is not None:
            trade.pnl = data.pnl
        else:
            if trade.direction == TradeDirection.BUY:
                trade.pnl = (data.exit_price - trade.entry_price) * trade.lot_size
            else:
                trade.pnl = (trade.entry_price - data.exit_price) * trade.lot_size

        updated = await self.trade_repo.update(trade)

        if updated.pnl is not None:
            account.current_balance += updated.pnl
            await self.account_repo.update(account)

        # Invalidate cache
        await self.analytics_service.invalidate_metrics_cache(account.id)

        response_dto = TradeResponse.model_validate(updated)

        event = TradeEventNotification(
            event_type="TRADE_CLOSED",
            account_id=account.id,
            trade=response_dto,
            timestamp=datetime.now(UTC),
        )
        event_dict = event.model_dump(mode="json")

        if self.redis_cache:
            await self.redis_cache.publish(f"account:{account.id}:events", event_dict)
        await ws_manager.broadcast_to_account(account.id, event_dict)

        return response_dto

    async def list_account_trades(
        self,
        account_id: uuid.UUID,
        user_id: uuid.UUID,
        status: TradeStatus | None = None,
        symbol: str | None = None,
        skip: int = 0,
        limit: int = 100,
    ) -> list[TradeResponse]:
        account = await self.account_repo.get_by_id(account_id)
        if not account:
            raise AccountNotFoundException(f"Trading account '{account_id}' not found.")
        if account.user_id != user_id:
            raise UnauthorizedAccessException(
                "You are not authorized to view trades for this account."
            )

        trades = await self.trade_repo.list_by_account(
            account_id=account_id,
            status=status,
            symbol=symbol,
            order_asc=False,
            skip=skip,
            limit=limit,
        )
        return [TradeResponse.model_validate(t) for t in trades]

    async def get_trade(self, trade_id: uuid.UUID, user_id: uuid.UUID) -> TradeResponse:
        trade = await self.trade_repo.get_by_id(trade_id)
        if not trade:
            raise TradeNotFoundException(f"Trade '{trade_id}' not found.")

        account = await self.account_repo.get_by_id(trade.account_id)
        if not account or account.user_id != user_id:
            raise UnauthorizedAccessException("You are not authorized to view this trade.")

        return TradeResponse.model_validate(trade)
