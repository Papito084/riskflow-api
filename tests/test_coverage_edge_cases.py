import uuid
from decimal import Decimal

import pytest
from httpx import AsyncClient

from src.core.config import Settings
from src.core.security import create_access_token
from src.domain.enums import TradeDirection
from src.domain.models import TradingAccount, User
from src.schemas.account import TradingAccountCreate
from src.schemas.trade import TradeCloseRequest, TradeCreate
from src.services.trade_service import TradeService


def test_cors_origins_parsing():
    settings_obj = Settings(CORS_ORIGINS="http://localhost:3000,http://localhost:4000")
    assert "http://localhost:3000" in settings_obj.CORS_ORIGINS
    assert "http://localhost:4000" in settings_obj.CORS_ORIGINS

    settings_json = Settings(CORS_ORIGINS='["http://localhost:5000"]')
    assert "http://localhost:5000" in settings_json.CORS_ORIGINS


@pytest.mark.asyncio
async def test_account_not_found_and_unauthorized(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
):
    non_existent_id = uuid.uuid4()
    # 404 on get
    res = await async_client.get(f"/api/v1/accounts/{non_existent_id}", headers=auth_headers)
    assert res.status_code == 404

    # 404 on patch
    res_patch = await async_client.patch(
        f"/api/v1/accounts/{non_existent_id}",
        headers=auth_headers,
        json={"name": "New Name"},
    )
    assert res_patch.status_code == 404


@pytest.mark.asyncio
async def test_trade_service_unauthorized_and_not_found(
    db_session,
    test_account: TradingAccount,
):
    service = TradeService(db_session)
    other_user_id = uuid.uuid4()

    # Create trade with unauthorized user
    with pytest.raises(Exception) as exc_info:
        await service.create_trade(
            user_id=other_user_id,
            data=TradeCreate(
                account_id=test_account.id,
                symbol="EURUSD",
                direction=TradeDirection.BUY,
                entry_price=Decimal("1.08"),
                lot_size=Decimal("1.0"),
            ),
        )
    assert "not authorized" in str(exc_info.value).lower()

    from src.domain.exceptions import TradeNotFoundException

    # Get trade not found
    with pytest.raises(TradeNotFoundException):
        await service.get_trade(uuid.uuid4(), test_account.user_id)

    # Close trade not found
    with pytest.raises(TradeNotFoundException):
        await service.close_trade(
            uuid.uuid4(), test_account.user_id, TradeCloseRequest(exit_price=Decimal("1.09"))
        )


@pytest.mark.asyncio
async def test_auth_refresh_invalid_token(async_client: AsyncClient, test_user: User):
    # Pass access token instead of refresh token
    access_token = create_access_token(subject=str(test_user.id))
    res = await async_client.post("/api/v1/auth/refresh", json={"refresh_token": access_token})
    assert res.status_code == 403

    # Pass garbage token
    res_garbage = await async_client.post(
        "/api/v1/auth/refresh", json={"refresh_token": "not-a-token"}
    )
    assert res_garbage.status_code == 403


@pytest.mark.asyncio
async def test_redis_service_operations():
    from src.core.redis import RedisCacheService

    class DummyRedis:
        def __init__(self):
            self.d = {}

        async def get(self, k):
            return self.d.get(k)

        async def set(self, k, v, ex=None):
            self.d[k] = v

        async def delete(self, k):
            self.d.pop(k, None)

        async def publish(self, ch, msg):
            return 1

    dummy = DummyRedis()
    svc = RedisCacheService(dummy)  # type: ignore[arg-type]
    await svc.set_json("test_key", {"foo": "bar"}, ttl=10)
    val = await svc.get_json("test_key")
    assert val == {"foo": "bar"}
    await svc.delete("test_key")
    assert await svc.get_json("test_key") is None
    pub_count = await svc.publish("test_ch", {"event": 1})
    assert pub_count == 1


@pytest.mark.asyncio
async def test_account_service_exceptions(db_session, test_user: User):
    from src.domain.exceptions import AccountNotFoundException, UnauthorizedAccessException
    from src.schemas.account import TradingAccountUpdate
    from src.services.account_service import AccountService

    svc = AccountService(db_session)
    non_existent = uuid.uuid4()
    other_user = uuid.uuid4()

    # Not found on get
    with pytest.raises(AccountNotFoundException):
        await svc.get_user_account(non_existent, test_user.id)

    # Not found on update
    with pytest.raises(AccountNotFoundException):
        await svc.update_account(non_existent, test_user.id, TradingAccountUpdate(name="Test"))

    # Unauthorized access on get
    account = await svc.create_account(
        test_user.id,
        TradingAccountCreate(name="Private", initial_balance=Decimal("1000.00")),
    )
    with pytest.raises(UnauthorizedAccessException):
        await svc.get_user_account(account.id, other_user)

    # Unauthorized access on update
    with pytest.raises(UnauthorizedAccessException):
        await svc.update_account(account.id, other_user, TradingAccountUpdate(name="Hacked"))


@pytest.mark.asyncio
async def test_trade_service_additional_exceptions(
    db_session, test_user: User, test_account: TradingAccount
):
    from src.domain.exceptions import (
        AccountNotFoundException,
        UnauthorizedAccessException,
    )
    from src.schemas.trade import TradeCloseRequest, TradeCreate
    from src.services.trade_service import TradeService

    svc = TradeService(db_session)
    other_user = uuid.uuid4()

    # Create trade with non-existent account
    with pytest.raises(AccountNotFoundException):
        await svc.create_trade(
            test_user.id,
            TradeCreate(
                account_id=uuid.uuid4(),
                symbol="EURUSD",
                direction=TradeDirection.BUY,
                entry_price=Decimal("1.08"),
                lot_size=Decimal("1.0"),
            ),
        )

    # List trades with non-existent account
    with pytest.raises(AccountNotFoundException):
        await svc.list_account_trades(uuid.uuid4(), test_user.id)

    # List trades unauthorized
    with pytest.raises(UnauthorizedAccessException):
        await svc.list_account_trades(test_account.id, other_user)

    # Create trade and test unauthorized get and close
    trade = await svc.create_trade(
        test_user.id,
        TradeCreate(
            account_id=test_account.id,
            symbol="EURUSD",
            direction=TradeDirection.BUY,
            entry_price=Decimal("1.08"),
            lot_size=Decimal("1.0"),
        ),
    )
    with pytest.raises(UnauthorizedAccessException):
        await svc.get_trade(trade.id, other_user)

    with pytest.raises(UnauthorizedAccessException):
        await svc.close_trade(trade.id, other_user, TradeCloseRequest(exit_price=Decimal("1.09")))


@pytest.mark.asyncio
async def test_deps_optional_current_user(db_session, test_user: User):
    from fastapi.security import HTTPAuthorizationCredentials

    from src.api.deps import get_optional_current_user
    from src.core.security import create_access_token

    # None credentials
    res_none = await get_optional_current_user(None, db_session)
    assert res_none is None

    # Valid credentials
    token = create_access_token(subject=str(test_user.id))
    creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)
    res_user = await get_optional_current_user(creds, db_session)
    assert res_user is not None
    assert res_user.id == test_user.id


def test_config_computed_properties():
    from src.core.config import Settings

    s1 = Settings(DATABASE_URL="postgresql+asyncpg://u:p@h:5432/db", REDIS_URL="redis://h:6379/1")
    assert s1.async_database_url == "postgresql+asyncpg://u:p@h:5432/db"
    assert s1.async_redis_url == "redis://h:6379/1"

    s2 = Settings(
        DATABASE_URL=None,
        REDIS_URL=None,
        POSTGRES_USER="test_u",
        POSTGRES_PASSWORD="test_p",
        POSTGRES_SERVER="test_h",
        POSTGRES_PORT=5432,
        POSTGRES_DB="test_db",
        REDIS_HOST="redis_h",
        REDIS_PORT=6379,
        REDIS_DB=2,
        REDIS_PASSWORD="secret",
    )
    assert "test_u:test_p@test_h:5432/test_db" in s2.async_database_url
    assert "redis://:secret@redis_h:6379/2" == s2.async_redis_url
