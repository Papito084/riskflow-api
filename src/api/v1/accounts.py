import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.deps import get_current_user
from src.core.database import get_db
from src.domain.models import User
from src.schemas.account import (
    TradingAccountCreate,
    TradingAccountResponse,
    TradingAccountUpdate,
)
from src.services.account_service import AccountService

router = APIRouter(prefix="/accounts", tags=["Trading Accounts"])


@router.post(
    "/",
    response_model=TradingAccountResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new trading account or portfolio",
)
async def create_account(
    data: TradingAccountCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> TradingAccountResponse:
    service = AccountService(session)
    return await service.create_account(current_user.id, data)


@router.get(
    "/",
    response_model=list[TradingAccountResponse],
    status_code=status.HTTP_200_OK,
    summary="List all trading accounts belonging to current user",
)
async def list_accounts(
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> list[TradingAccountResponse]:
    service = AccountService(session)
    return await service.list_user_accounts(current_user.id)


@router.get(
    "/{account_id}",
    response_model=TradingAccountResponse,
    status_code=status.HTTP_200_OK,
    summary="Get details of a specific trading account",
)
async def get_account(
    account_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> TradingAccountResponse:
    service = AccountService(session)
    return await service.get_user_account(account_id, current_user.id)


@router.patch(
    "/{account_id}",
    response_model=TradingAccountResponse,
    status_code=status.HTTP_200_OK,
    summary="Update trading account settings",
)
async def update_account(
    account_id: uuid.UUID,
    data: TradingAccountUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> TradingAccountResponse:
    service = AccountService(session)
    return await service.update_account(account_id, current_user.id, data)
