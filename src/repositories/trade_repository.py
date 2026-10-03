import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.enums import TradeStatus
from src.domain.models import Trade
from src.repositories.base import BaseRepository


class TradeRepository(BaseRepository[Trade]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(Trade, session)

    async def list_by_account(
        self,
        account_id: uuid.UUID,
        status: TradeStatus | None = None,
        symbol: str | None = None,
        order_asc: bool = True,
        skip: int = 0,
        limit: int = 500,
    ) -> list[Trade]:
        stmt = select(Trade).where(Trade.account_id == account_id)
        if status:
            stmt = stmt.where(Trade.status == status)
        if symbol:
            stmt = stmt.where(Trade.symbol == symbol.upper().strip())

        if order_asc:
            stmt = stmt.order_by(Trade.opened_at.asc())
        else:
            stmt = stmt.order_by(Trade.opened_at.desc())

        stmt = stmt.offset(skip).limit(limit)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_id_and_account(
        self, trade_id: uuid.UUID, account_id: uuid.UUID
    ) -> Trade | None:
        stmt = select(Trade).where(
            Trade.id == trade_id,
            Trade.account_id == account_id,
        )
        result = await self.session.execute(stmt)
        return result.scalars().first()
