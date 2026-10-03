import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.exceptions import AccountNotFoundException, UnauthorizedAccessException
from src.domain.models import TradingAccount
from src.repositories.account_repository import AccountRepository
from src.schemas.account import (
    TradingAccountCreate,
    TradingAccountResponse,
    TradingAccountUpdate,
)


class AccountService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.account_repo = AccountRepository(session)

    async def create_account(
        self, user_id: uuid.UUID, data: TradingAccountCreate
    ) -> TradingAccountResponse:
        account = TradingAccount(
            user_id=user_id,
            name=data.name,
            broker_type=data.broker_type,
            initial_balance=data.initial_balance,
            current_balance=data.initial_balance,
            currency=data.currency,
        )
        created = await self.account_repo.create(account)
        return TradingAccountResponse.model_validate(created)

    async def list_user_accounts(self, user_id: uuid.UUID) -> list[TradingAccountResponse]:
        accounts = await self.account_repo.get_by_user_id(user_id)
        return [TradingAccountResponse.model_validate(acc) for acc in accounts]

    async def get_user_account(
        self, account_id: uuid.UUID, user_id: uuid.UUID
    ) -> TradingAccountResponse:
        account = await self.account_repo.get_by_id(account_id)
        if not account:
            raise AccountNotFoundException(f"Trading account with ID '{account_id}' was not found.")
        if account.user_id != user_id:
            raise UnauthorizedAccessException(
                "You do not have permission to access this trading account."
            )
        return TradingAccountResponse.model_validate(account)

    async def update_account(
        self, account_id: uuid.UUID, user_id: uuid.UUID, data: TradingAccountUpdate
    ) -> TradingAccountResponse:
        account = await self.account_repo.get_by_id(account_id)
        if not account:
            raise AccountNotFoundException(f"Trading account with ID '{account_id}' was not found.")
        if account.user_id != user_id:
            raise UnauthorizedAccessException(
                "You do not have permission to modify this trading account."
            )

        if data.name is not None:
            account.name = data.name
        if data.broker_type is not None:
            account.broker_type = data.broker_type

        updated = await self.account_repo.update(account)
        return TradingAccountResponse.model_validate(updated)
