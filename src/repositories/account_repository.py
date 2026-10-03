import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.models import TradingAccount
from src.repositories.base import BaseRepository


class AccountRepository(BaseRepository[TradingAccount]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(TradingAccount, session)

    async def get_by_user_id(self, user_id: uuid.UUID) -> list[TradingAccount]:
        stmt = (
            select(TradingAccount)
            .where(TradingAccount.user_id == user_id)
            .order_by(TradingAccount.created_at.asc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_user_account(
        self, account_id: uuid.UUID, user_id: uuid.UUID
    ) -> TradingAccount | None:
        stmt = select(TradingAccount).where(
            TradingAccount.id == account_id,
            TradingAccount.user_id == user_id,
        )
        result = await self.session.execute(stmt)
        return result.scalars().first()
