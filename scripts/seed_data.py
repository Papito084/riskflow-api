import asyncio
import logging
import random
from datetime import UTC, datetime, timedelta
from decimal import Decimal

from sqlalchemy import select

from src.core.database import async_session_factory
from src.core.security import get_password_hash
from src.domain.enums import BrokerType, Currency, TradeDirection, TradeStatus
from src.domain.models import Trade, TradingAccount, User

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("seed")


ASSETS = [
    {
        "symbol": "XAUUSD",
        "base_price": Decimal("2350.00"),
        "spread": Decimal("25.00"),
        "lot": Decimal("2.0"),
    },
    {
        "symbol": "EURUSD",
        "base_price": Decimal("1.0850"),
        "spread": Decimal("0.0040"),
        "lot": Decimal("1.5"),
    },
    {
        "symbol": "GBPUSD",
        "base_price": Decimal("1.2720"),
        "spread": Decimal("0.0050"),
        "lot": Decimal("1.0"),
    },
    {
        "symbol": "US100",
        "base_price": Decimal("19200.00"),
        "spread": Decimal("150.00"),
        "lot": Decimal("0.5"),
    },
    {
        "symbol": "BTCUSD",
        "base_price": Decimal("64000.00"),
        "spread": Decimal("800.00"),
        "lot": Decimal("0.1"),
    },
]


async def seed() -> None:
    logger.info("Starting database seeding...")

    async with async_session_factory() as session:
        # 1. Check or create demo user
        stmt = select(User).where(User.email == "demo@riskflow.io")
        result = await session.execute(stmt)
        user = result.scalars().first()

        if user:
            logger.info("Demo user 'demo@riskflow.io' already exists. Skipping duplicate seeding.")
            return

        user = User(
            email="demo@riskflow.io",
            hashed_password=get_password_hash("DemoPassword123!"),
        )
        session.add(user)
        await session.flush()
        await session.refresh(user)
        logger.info("Created Demo User: %s (Password: DemoPassword123!)", user.email)

        # 2. Create Two Trading Accounts
        prop_account = TradingAccount(
            user_id=user.id,
            name="FTMO Funded $100k",
            broker_type=BrokerType.PROP_FIRM,
            initial_balance=Decimal("100000.00"),
            current_balance=Decimal("100000.00"),
            currency=Currency.USD,
        )
        personal_account = TradingAccount(
            user_id=user.id,
            name="Interactive Brokers Swing Portfolio",
            broker_type=BrokerType.PERSONAL,
            initial_balance=Decimal("25000.00"),
            current_balance=Decimal("25000.00"),
            currency=Currency.EUR,
        )
        session.add_all([prop_account, personal_account])
        await session.flush()
        await session.refresh(prop_account)
        await session.refresh(personal_account)
        logger.info("Created Accounts: '%s' and '%s'", prop_account.name, personal_account.name)

        # 3. Generate 50 Realistic Simulated Trades for the Prop Account
        random.seed(42)  # Deterministic seed for reproducible testing
        base_date = datetime.now(UTC) - timedelta(days=45)
        cumulative_pnl = Decimal("0.00")

        trades: list[Trade] = []

        # 45 Closed Trades + 5 Open Trades
        for i in range(50):
            asset = random.choice(ASSETS)
            direction = random.choice([TradeDirection.BUY, TradeDirection.SELL])
            lot_size = asset["lot"]
            opened_at = base_date + timedelta(hours=i * 20, minutes=random.randint(5, 55))

            entry_price = asset["base_price"] + Decimal(str(random.randint(-100, 100))) * (
                asset["spread"] / Decimal("10")
            )
            entry_price = entry_price.quantize(Decimal("0.0001"))

            is_open = i >= 45  # Last 5 trades are open

            if is_open:
                trade = Trade(
                    account_id=prop_account.id,
                    symbol=asset["symbol"],
                    direction=direction,
                    entry_price=entry_price,
                    exit_price=None,
                    lot_size=lot_size,
                    pnl=None,
                    opened_at=opened_at,
                    closed_at=None,
                    status=TradeStatus.OPEN,
                )
            else:
                closed_at = opened_at + timedelta(
                    hours=random.randint(1, 8), minutes=random.randint(10, 50)
                )
                # 58% Win Rate
                is_win = random.random() < 0.58

                if is_win:
                    pnl_magnitude = Decimal(str(random.randint(450, 1800)))
                    pnl = pnl_magnitude
                    price_delta = (pnl / (lot_size * Decimal("100"))).quantize(Decimal("0.0001"))
                    exit_price = (
                        (entry_price + price_delta)
                        if direction == TradeDirection.BUY
                        else (entry_price - price_delta)
                    )
                else:
                    pnl_magnitude = Decimal(str(random.randint(300, 950)))
                    pnl = -pnl_magnitude
                    price_delta = (pnl_magnitude / (lot_size * Decimal("100"))).quantize(
                        Decimal("0.0001")
                    )
                    exit_price = (
                        (entry_price - price_delta)
                        if direction == TradeDirection.BUY
                        else (entry_price + price_delta)
                    )

                exit_price = max(exit_price, Decimal("0.0001"))
                cumulative_pnl += pnl

                trade = Trade(
                    account_id=prop_account.id,
                    symbol=asset["symbol"],
                    direction=direction,
                    entry_price=entry_price,
                    exit_price=exit_price,
                    lot_size=lot_size,
                    pnl=pnl,
                    opened_at=opened_at,
                    closed_at=closed_at,
                    status=TradeStatus.CLOSED,
                )

            trades.append(trade)

        session.add_all(trades)
        prop_account.current_balance = prop_account.initial_balance + cumulative_pnl
        session.add(prop_account)

        await session.commit()
        logger.info(
            "Seeded 50 trades (45 closed, 5 open) with net PnL: $%s. Final Balance: $%s",
            cumulative_pnl,
            prop_account.current_balance,
        )
        logger.info("Database seeding completed successfully!")


if __name__ == "__main__":
    asyncio.run(seed())
