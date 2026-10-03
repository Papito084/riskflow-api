import uuid
from typing import Annotated

import redis.asyncio as aioredis
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.deps import get_current_user
from src.core.database import get_db
from src.core.redis import get_redis
from src.domain.enums import TradeStatus
from src.domain.models import User
from src.schemas.trade import (
    TradeCloseRequest,
    TradeCreate,
    TradeResponse,
)
from src.services.trade_service import TradeService

router = APIRouter(prefix="/trades", tags=["Trades"])


@router.post(
    "/",
    response_model=TradeResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Ingest a new trade into a trading account",
)
async def create_trade(
    data: TradeCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
    redis: Annotated[aioredis.Redis, Depends(get_redis)],
) -> TradeResponse:
    service = TradeService(session, redis)
    return await service.create_trade(current_user.id, data)


@router.post(
    "/{trade_id}/close",
    response_model=TradeResponse,
    status_code=status.HTTP_200_OK,
    summary="Close an open trade with exit price and compute realized PnL",
)
async def close_trade(
    trade_id: uuid.UUID,
    data: TradeCloseRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
    redis: Annotated[aioredis.Redis, Depends(get_redis)],
) -> TradeResponse:
    service = TradeService(session, redis)
    return await service.close_trade(trade_id, current_user.id, data)


@router.get(
    "/account/{account_id}",
    response_model=list[TradeResponse],
    status_code=status.HTTP_200_OK,
    summary="List trades for a specific account with optional filters",
)
async def list_account_trades(
    account_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
    status_filter: TradeStatus | None = Query(None, alias="status"),
    symbol: str | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
) -> list[TradeResponse]:
    service = TradeService(session)
    return await service.list_account_trades(
        account_id=account_id,
        user_id=current_user.id,
        status=status_filter,
        symbol=symbol,
        skip=skip,
        limit=limit,
    )


@router.get(
    "/{trade_id}",
    response_model=TradeResponse,
    status_code=status.HTTP_200_OK,
    summary="Get single trade by ID",
)
async def get_trade(
    trade_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> TradeResponse:
    service = TradeService(session)
    return await service.get_trade(trade_id, current_user.id)
