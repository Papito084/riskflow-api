class DomainException(Exception):
    """Base exception for all domain business errors."""

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class EntityNotFoundException(DomainException):
    """Base exception for entities not found in persistence."""

    pass


class UserAlreadyExistsException(DomainException):
    """Raised when an email is already registered."""

    pass


class InvalidCredentialsException(DomainException):
    """Raised when authentication credentials do not match."""

    pass


class AccountNotFoundException(EntityNotFoundException):
    """Raised when a trading account does not exist."""

    pass


class TradeNotFoundException(EntityNotFoundException):
    """Raised when a trade does not exist."""

    pass


class InvalidTradeStateException(DomainException):
    """Raised when a trade transition is illegal (e.g. closing an already closed trade)."""

    pass


class UnauthorizedAccessException(DomainException):
    """Raised when a user attempts to access an entity they do not own."""

    pass
