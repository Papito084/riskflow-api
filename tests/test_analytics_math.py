import uuid
from datetime import UTC, datetime, timedelta
from decimal import Decimal

from src.domain.enums import TradeDirection, TradeStatus
from src.domain.models import Trade
from src.services.analytics import RiskAnalyticsEngine


def make_dummy_trade(
    pnl: Decimal | None,
    status: TradeStatus = TradeStatus.CLOSED,
    opened_offset_minutes: int = 0,
) -> Trade:
    opened_at = datetime(2026, 1, 1, 10, 0, 0, tzinfo=UTC) + timedelta(
        minutes=opened_offset_minutes
    )
    return Trade(
        id=uuid.uuid4(),
        account_id=uuid.uuid4(),
        symbol="EURUSD",
        direction=TradeDirection.BUY,
        entry_price=Decimal("1.08000"),
        exit_price=Decimal("1.08500") if status == TradeStatus.CLOSED else None,
        lot_size=Decimal("1.00"),
        pnl=pnl,
        opened_at=opened_at,
        closed_at=opened_at + timedelta(minutes=30) if status == TradeStatus.CLOSED else None,
        status=status,
    )


def test_calculate_metrics_zero_trades():
    account_id = uuid.uuid4()
    initial_balance = Decimal("10000.00")
    trades: list[Trade] = []

    metrics = RiskAnalyticsEngine.calculate_metrics(account_id, initial_balance, trades)

    assert metrics.account_id == account_id
    assert metrics.total_trades == 0
    assert metrics.closed_trades == 0
    assert metrics.open_trades == 0
    assert metrics.win_rate_pct == Decimal("0.00")
    assert metrics.loss_rate_pct == Decimal("0.00")
    assert metrics.gross_profit == Decimal("0.00")
    assert metrics.gross_loss == Decimal("0.00")
    assert metrics.net_profit == Decimal("0.00")
    assert metrics.profit_factor is None
    assert metrics.max_drawdown_amount == Decimal("0.00")
    assert metrics.max_drawdown_pct == Decimal("0.00")
    assert metrics.risk_reward_ratio is None
    assert metrics.expectancy == Decimal("0.00")


def test_calculate_metrics_only_open_trades():
    account_id = uuid.uuid4()
    initial_balance = Decimal("10000.00")
    trades = [
        make_dummy_trade(pnl=None, status=TradeStatus.OPEN),
        make_dummy_trade(pnl=None, status=TradeStatus.OPEN),
    ]

    metrics = RiskAnalyticsEngine.calculate_metrics(account_id, initial_balance, trades)

    assert metrics.total_trades == 2
    assert metrics.closed_trades == 0
    assert metrics.open_trades == 2
    assert metrics.win_rate_pct == Decimal("0.00")


def test_calculate_metrics_all_winning_trades():
    account_id = uuid.uuid4()
    initial_balance = Decimal("10000.00")
    trades = [
        make_dummy_trade(pnl=Decimal("200.00"), opened_offset_minutes=10),
        make_dummy_trade(pnl=Decimal("300.00"), opened_offset_minutes=20),
        make_dummy_trade(pnl=Decimal("500.00"), opened_offset_minutes=30),
    ]

    metrics = RiskAnalyticsEngine.calculate_metrics(account_id, initial_balance, trades)

    assert metrics.total_trades == 3
    assert metrics.closed_trades == 3
    assert metrics.winning_trades == 3
    assert metrics.losing_trades == 0
    assert metrics.win_rate_pct == Decimal("100.00")
    assert metrics.loss_rate_pct == Decimal("0.00")
    assert metrics.gross_profit == Decimal("1000.00")
    assert metrics.gross_loss == Decimal("0.00")
    assert metrics.net_profit == Decimal("1000.00")
    assert metrics.profit_factor is None  # Undefined when no losses
    assert metrics.max_drawdown_amount == Decimal("0.00")
    assert metrics.max_drawdown_pct == Decimal("0.00")
    assert metrics.average_win == Decimal("333.33")
    assert metrics.average_loss == Decimal("0.00")
    assert metrics.risk_reward_ratio is None
    # Expectancy: (1.0 * 333.33) - 0 = 333.33
    assert metrics.expectancy == Decimal("333.33")


def test_calculate_metrics_all_losing_trades():
    account_id = uuid.uuid4()
    initial_balance = Decimal("10000.00")
    trades = [
        make_dummy_trade(pnl=Decimal("-100.00"), opened_offset_minutes=10),
        make_dummy_trade(pnl=Decimal("-200.00"), opened_offset_minutes=20),
    ]

    metrics = RiskAnalyticsEngine.calculate_metrics(account_id, initial_balance, trades)

    assert metrics.closed_trades == 2
    assert metrics.winning_trades == 0
    assert metrics.losing_trades == 2
    assert metrics.win_rate_pct == Decimal("0.00")
    assert metrics.loss_rate_pct == Decimal("100.00")
    assert metrics.gross_profit == Decimal("0.00")
    assert metrics.gross_loss == Decimal("300.00")
    assert metrics.net_profit == Decimal("-300.00")
    assert metrics.profit_factor == Decimal("0.0000")
    assert metrics.average_loss == Decimal("150.00")
    # Drawdown: initial 10000 -> 9900 -> 9700. Max DD = 300 (3.00%)
    assert metrics.max_drawdown_amount == Decimal("300.00")
    assert metrics.max_drawdown_pct == Decimal("3.00")
    assert metrics.expectancy == Decimal("-150.00")


def test_calculate_metrics_mixed_series_and_drawdown():
    # Sequence of trades with peak and trough:
    # Initial: 10,000
    # T1: +1000 -> equity: 11,000 (new peak: 11,000)
    # T2: -500  -> equity: 10,500 (DD: 500 / 11,000 = 4.5455%)
    # T3: -1000 -> equity: 9,500  (DD: 1500 / 11,000 = 13.6364%)
    # T4: +2500 -> equity: 12,000 (new peak: 12,000)
    # T5: -600  -> equity: 11,400 (DD: 600 / 12,000 = 5.0000%)
    account_id = uuid.uuid4()
    initial_balance = Decimal("10000.00")
    trades = [
        make_dummy_trade(pnl=Decimal("1000.00"), opened_offset_minutes=10),
        make_dummy_trade(pnl=Decimal("-500.00"), opened_offset_minutes=20),
        make_dummy_trade(pnl=Decimal("-1000.00"), opened_offset_minutes=30),
        make_dummy_trade(pnl=Decimal("2500.00"), opened_offset_minutes=40),
        make_dummy_trade(pnl=Decimal("-600.00"), opened_offset_minutes=50),
    ]

    metrics = RiskAnalyticsEngine.calculate_metrics(account_id, initial_balance, trades)

    assert metrics.total_trades == 5
    assert metrics.closed_trades == 5
    assert metrics.winning_trades == 2
    assert metrics.losing_trades == 3
    # Win rate: 2/5 = 40.00%
    assert metrics.win_rate_pct == Decimal("40.00")
    # Loss rate: 3/5 = 60.00%
    assert metrics.loss_rate_pct == Decimal("60.00")

    # Gross profit: 1000 + 2500 = 3500.00
    assert metrics.gross_profit == Decimal("3500.00")
    # Gross loss: 500 + 1000 + 600 = 2100.00
    assert metrics.gross_loss == Decimal("2100.00")
    # Net profit: 3500 - 2100 = 1400.00
    assert metrics.net_profit == Decimal("1400.00")

    # Profit factor: 3500 / 2100 = 1.6667
    assert metrics.profit_factor == Decimal("1.6667")

    # Average win: 3500 / 2 = 1750.00
    assert metrics.average_win == Decimal("1750.00")
    # Average loss: 2100 / 3 = 700.00
    assert metrics.average_loss == Decimal("700.00")

    # Risk / Reward ratio: 1750 / 700 = 2.5000
    assert metrics.risk_reward_ratio == Decimal("2.5000")

    # Expectancy: (0.40 * 1750) - (0.60 * 700) = 700 - 420 = 280.00
    # Net Profit / 5 = 1400 / 5 = 280.00
    assert metrics.expectancy == Decimal("280.00")

    # Max Drawdown: 1500.00 from peak of 11,000.00 -> 1500 / 11000 * 100 = 13.64%
    assert metrics.max_drawdown_amount == Decimal("1500.00")
    assert metrics.max_drawdown_pct == Decimal("13.64")
