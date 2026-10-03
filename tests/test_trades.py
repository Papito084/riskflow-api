import uuid

import pytest
from httpx import AsyncClient

from src.domain.models import TradingAccount


@pytest.mark.asyncio
async def test_create_and_list_accounts(async_client: AsyncClient, auth_headers: dict[str, str]):
    create_res = await async_client.post(
        "/api/v1/accounts/",
        headers=auth_headers,
        json={
            "name": "Swing Trading Account",
            "broker_type": "Personal",
            "initial_balance": "50000.00",
            "currency": "EUR",
        },
    )
    assert create_res.status_code == 201
    account = create_res.json()
    assert account["name"] == "Swing Trading Account"
    assert account["broker_type"] == "Personal"
    assert account["initial_balance"] == "50000.00"

    list_res = await async_client.get("/api/v1/accounts/", headers=auth_headers)
    assert list_res.status_code == 200
    accounts = list_res.json()
    assert len(accounts) >= 1


@pytest.mark.asyncio
async def test_ingest_open_trade(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
    test_account: TradingAccount,
):
    trade_payload = {
        "account_id": str(test_account.id),
        "symbol": "XAUUSD",
        "direction": "BUY",
        "entry_price": "2350.50",
        "lot_size": "2.0",
        "status": "OPEN",
    }
    response = await async_client.post("/api/v1/trades/", headers=auth_headers, json=trade_payload)
    assert response.status_code == 201
    data = response.json()
    assert data["symbol"] == "XAUUSD"
    assert data["status"] == "OPEN"
    assert data["exit_price"] is None
    assert data["pnl"] is None


@pytest.mark.asyncio
async def test_close_trade_and_update_balance(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
    test_account: TradingAccount,
):
    # 1. Create open trade
    trade_res = await async_client.post(
        "/api/v1/trades/",
        headers=auth_headers,
        json={
            "account_id": str(test_account.id),
            "symbol": "EURUSD",
            "direction": "BUY",
            "entry_price": "1.08500",
            "lot_size": "1.0",
            "status": "OPEN",
        },
    )
    trade_id = trade_res.json()["id"]

    # 2. Close trade with profit
    close_res = await async_client.post(
        f"/api/v1/trades/{trade_id}/close",
        headers=auth_headers,
        json={
            "exit_price": "1.09000",
            "pnl": "500.00",
        },
    )
    assert close_res.status_code == 200
    closed_trade = close_res.json()
    assert closed_trade["status"] == "CLOSED"
    assert closed_trade["pnl"] == "500.00"

    # 3. Verify account balance was credited
    acc_res = await async_client.get(f"/api/v1/accounts/{test_account.id}", headers=auth_headers)
    assert acc_res.status_code == 200
    updated_acc = acc_res.json()
    # 100,000 + 500 = 100500.00
    assert updated_acc["current_balance"] == "100500.00"


@pytest.mark.asyncio
async def test_get_analytics_endpoint(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
    test_account: TradingAccount,
):
    # Create two closed trades: 1 win (+1200), 1 loss (-400)
    await async_client.post(
        "/api/v1/trades/",
        headers=auth_headers,
        json={
            "account_id": str(test_account.id),
            "symbol": "US100",
            "direction": "BUY",
            "entry_price": "19000.00",
            "exit_price": "19200.00",
            "lot_size": "1.0",
            "pnl": "1200.00",
            "status": "CLOSED",
        },
    )
    await async_client.post(
        "/api/v1/trades/",
        headers=auth_headers,
        json={
            "account_id": str(test_account.id),
            "symbol": "US100",
            "direction": "SELL",
            "entry_price": "19200.00",
            "exit_price": "19400.00",
            "lot_size": "1.0",
            "pnl": "-400.00",
            "status": "CLOSED",
        },
    )

    analytics_res = await async_client.get(
        f"/api/v1/analytics/accounts/{test_account.id}",
        headers=auth_headers,
    )
    assert analytics_res.status_code == 200
    metrics = analytics_res.json()
    assert metrics["closed_trades"] == 2
    assert metrics["winning_trades"] == 1
    assert metrics["losing_trades"] == 1
    assert metrics["win_rate_pct"] == "50.00"
    assert metrics["gross_profit"] == "1200.00"
    assert metrics["gross_loss"] == "400.00"
    assert metrics["net_profit"] == "800.00"
    assert metrics["profit_factor"] == "3.0000"
    assert metrics["risk_reward_ratio"] == "3.0000"


@pytest.mark.asyncio
async def test_unauthorized_access_to_account(async_client: AsyncClient):
    random_account_id = uuid.uuid4()
    # Unauthenticated request
    res = await async_client.get(f"/api/v1/accounts/{random_account_id}")
    assert res.status_code == 401


@pytest.mark.asyncio
async def test_update_account(
    async_client: AsyncClient, auth_headers: dict[str, str], test_account: TradingAccount
):
    res = await async_client.patch(
        f"/api/v1/accounts/{test_account.id}",
        headers=auth_headers,
        json={"name": "Renamed Account", "broker_type": "Personal"},
    )
    assert res.status_code == 200
    assert res.json()["name"] == "Renamed Account"
    assert res.json()["broker_type"] == "Personal"


@pytest.mark.asyncio
async def test_list_trades_with_filters_and_get_trade(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
    test_account: TradingAccount,
):
    # Ingest 1 BUY EURUSD, 1 SELL GBPUSD
    t1 = await async_client.post(
        "/api/v1/trades/",
        headers=auth_headers,
        json={
            "account_id": str(test_account.id),
            "symbol": "EURUSD",
            "direction": "BUY",
            "entry_price": "1.08000",
            "lot_size": "1.0",
            "status": "OPEN",
        },
    )
    assert t1.status_code == 201
    trade_id = t1.json()["id"]

    await async_client.post(
        "/api/v1/trades/",
        headers=auth_headers,
        json={
            "account_id": str(test_account.id),
            "symbol": "GBPUSD",
            "direction": "SELL",
            "entry_price": "1.27000",
            "exit_price": "1.26500",
            "lot_size": "1.0",
            "pnl": "500.00",
            "status": "CLOSED",
        },
    )

    # Filter by symbol
    res_symbol = await async_client.get(
        f"/api/v1/trades/account/{test_account.id}?symbol=EURUSD",
        headers=auth_headers,
    )
    assert res_symbol.status_code == 200
    assert len(res_symbol.json()) >= 1
    assert all(t["symbol"] == "EURUSD" for t in res_symbol.json())

    # Filter by status
    res_status = await async_client.get(
        f"/api/v1/trades/account/{test_account.id}?status=OPEN",
        headers=auth_headers,
    )
    assert res_status.status_code == 200
    assert len(res_status.json()) >= 1
    assert all(t["status"] == "OPEN" for t in res_status.json())

    # Get single trade
    res_single = await async_client.get(f"/api/v1/trades/{trade_id}", headers=auth_headers)
    assert res_single.status_code == 200
    assert res_single.json()["id"] == trade_id


@pytest.mark.asyncio
async def test_close_trade_sell_and_already_closed_error(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
    test_account: TradingAccount,
):
    # Create SELL trade
    sell_res = await async_client.post(
        "/api/v1/trades/",
        headers=auth_headers,
        json={
            "account_id": str(test_account.id),
            "symbol": "US30",
            "direction": "SELL",
            "entry_price": "39500.00",
            "lot_size": "1.0",
            "status": "OPEN",
        },
    )
    sell_trade_id = sell_res.json()["id"]

    # Close with automatic pnl calculation for SELL:
    # (entry - exit) * lot = (39500 - 39000) * 1 = +500
    close_res = await async_client.post(
        f"/api/v1/trades/{sell_trade_id}/close",
        headers=auth_headers,
        json={"exit_price": "39000.00"},
    )
    assert close_res.status_code == 200
    assert close_res.json()["pnl"] == "500.00"

    # Attempt to close again -> should fail with 400 BAD_REQUEST
    repeat_close = await async_client.post(
        f"/api/v1/trades/{sell_trade_id}/close",
        headers=auth_headers,
        json={"exit_price": "38900.00"},
    )
    assert repeat_close.status_code == 400


@pytest.mark.asyncio
async def test_analytics_redis_cache_hit(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
    test_account: TradingAccount,
):
    # First call: computes and caches (cached=False)
    res1 = await async_client.get(
        f"/api/v1/analytics/accounts/{test_account.id}",
        headers=auth_headers,
    )
    assert res1.status_code == 200
    assert res1.json()["cached"] is False

    # Second call: reads from cache (cached=True)
    res2 = await async_client.get(
        f"/api/v1/analytics/accounts/{test_account.id}",
        headers=auth_headers,
    )
    assert res2.status_code == 200
    assert res2.json()["cached"] is True


@pytest.mark.asyncio
async def test_health_check_endpoint(async_client: AsyncClient):
    res = await async_client.get("/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "healthy"
    assert "RiskFlow API" in data["service"]
