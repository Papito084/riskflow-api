import asyncio
from collections.abc import AsyncGenerator
from decimal import Decimal

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.api.deps import get_db, get_redis
from src.core.database import Base
from src.core.security import get_password_hash
from src.domain.enums import BrokerType, Currency
from src.domain.models import TradingAccount, User
from src.main import app

# In-memory SQLite async engine for lightning fast and isolated testing
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(
    TEST_DATABASE_URL,
    echo=False,
    future=True,
)

TestingSessionLocal = async_sessionmaker(
    bind=test_engine,
    class_=AsyncSession,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
)


class MockRedis:
    """Mock Redis client for testing caching and pub/sub."""

    def __init__(self) -> None:
        self.storage: dict[str, str] = {}

    async def get(self, key: str) -> str | None:
        return self.storage.get(key)

    async def set(self, key: str, value: str, ex: int | None = None) -> bool:
        self.storage[key] = value
        return True

    async def delete(self, key: str) -> int:
        if key in self.storage:
            del self.storage[key]
            return 1
        return 0

    async def publish(self, channel: str, message: str) -> int:
        return 1

    async def ping(self) -> bool:
        return True

    async def aclose(self) -> None:
        pass


mock_redis_client = MockRedis()


async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
    async with TestingSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def override_get_redis() -> MockRedis:
    return mock_redis_client


app.dependency_overrides[get_db] = override_get_db
app.dependency_overrides[get_redis] = override_get_redis


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(autouse=True)
async def prepare_database() -> AsyncGenerator[None, None]:
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    async with TestingSessionLocal() as session:
        yield session


@pytest.fixture
async def async_client() -> AsyncGenerator[AsyncClient, None]:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        yield client


@pytest.fixture
async def test_user(db_session: AsyncSession) -> User:
    user = User(
        email="trader@example.com",
        hashed_password=get_password_hash("password123"),
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def auth_headers(async_client: AsyncClient, test_user: User) -> dict[str, str]:
    login_response = await async_client.post(
        "/api/v1/auth/login",
        json={"email": "trader@example.com", "password": "password123"},
    )
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
async def test_account(db_session: AsyncSession, test_user: User) -> TradingAccount:
    account = TradingAccount(
        user_id=test_user.id,
        name="Main Prop Firm",
        broker_type=BrokerType.PROP_FIRM,
        initial_balance=Decimal("100000.00"),
        current_balance=Decimal("100000.00"),
        currency=Currency.USD,
    )
    db_session.add(account)
    await db_session.commit()
    await db_session.refresh(account)
    return account
