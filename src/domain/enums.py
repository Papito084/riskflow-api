from enum import StrEnum


class BrokerType(StrEnum):
    PROP_FIRM = "PropFirm"
    PERSONAL = "Personal"


class Currency(StrEnum):
    USD = "USD"
    EUR = "EUR"


class TradeDirection(StrEnum):
    BUY = "BUY"
    SELL = "SELL"


class TradeStatus(StrEnum):
    OPEN = "OPEN"
    CLOSED = "CLOSED"
