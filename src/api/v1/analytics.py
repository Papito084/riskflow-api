import uuid
from typing import Annotated

import redis.asyncio as aioredis
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.deps import get_current_user
from src.core.database import get_db
from src.core.redis import get_redis
from src.domain.exceptions import AccountNotFoundException, UnauthorizedAccessException
from src.domain.models import User
from src.repositories.account_repository import AccountRepository
from src.repositories.trade_repository import TradeRepository
from src.schemas.analytics import RiskMetricsResponse
from src.services.analytics import AnalyticsService

router = APIRouter(prefix="/analytics", tags=["Risk Analytics"])


@router.get(
    "/accounts/{account_id}",
    response_model=RiskMetricsResponse,
    status_code=status.HTTP_200_OK,
    summary="Calculate and return comprehensive portfolio risk metrics with Redis caching",
)
async def get_account_risk_metrics(
    account_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
    redis: Annotated[aioredis.Redis, Depends(get_redis)],
) -> RiskMetricsResponse:
    account_repo = AccountRepository(session)
    account = await account_repo.get_by_id(account_id)
    if not account:
        raise AccountNotFoundException(f"Trading account '{account_id}' was not found.")
    if account.user_id != current_user.id:
        raise UnauthorizedAccessException(
            "You are not authorized to view analytics for this account."
        )

    trade_repo = TradeRepository(session)
    trades = await trade_repo.list_by_account(account_id=account_id, order_asc=True, limit=5000)

    service = AnalyticsService(redis)
    return await service.get_account_metrics(
        account_id=account.id,
        initial_balance=account.initial_balance,
        trades=trades,
    )
