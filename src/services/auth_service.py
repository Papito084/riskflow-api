import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import settings
from src.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    get_password_hash,
    verify_password,
)
from src.domain.exceptions import (
    InvalidCredentialsException,
    UnauthorizedAccessException,
    UserAlreadyExistsException,
)
from src.domain.models import User
from src.repositories.user_repository import UserRepository
from src.schemas.auth import (
    RefreshTokenRequest,
    TokenResponse,
    UserLoginRequest,
    UserRegisterRequest,
    UserResponse,
)


class AuthService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.user_repo = UserRepository(session)

    async def register_user(self, data: UserRegisterRequest) -> UserResponse:
        existing = await self.user_repo.get_by_email(data.email)
        if existing:
            raise UserAlreadyExistsException(f"User with email '{data.email}' already exists.")

        hashed_pwd = get_password_hash(data.password)
        new_user = User(
            email=data.email.lower().strip(),
            hashed_password=hashed_pwd,
        )
        created_user = await self.user_repo.create(new_user)
        return UserResponse.model_validate(created_user)

    async def login_user(self, data: UserLoginRequest) -> TokenResponse:
        user = await self.user_repo.get_by_email(data.email)
        if not user:
            raise InvalidCredentialsException("Invalid email or password.")

        if not verify_password(data.password, user.hashed_password):
            raise InvalidCredentialsException("Invalid email or password.")

        access_token = create_access_token(
            subject=str(user.id),
            claims={"email": user.email},
        )
        refresh_token = create_refresh_token(subject=str(user.id))

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )

    async def refresh_tokens(self, data: RefreshTokenRequest) -> TokenResponse:
        try:
            payload = decode_token(data.refresh_token)
            if payload.get("type") != "refresh":
                raise UnauthorizedAccessException("Invalid token type. Expected refresh token.")
            user_id = payload.get("sub")
            if not user_id:
                raise UnauthorizedAccessException("Malformed refresh token.")
        except Exception as e:
            raise UnauthorizedAccessException(f"Could not validate refresh token: {e}") from e

        user = await self.user_repo.get_by_id(uuid.UUID(user_id))
        if not user:
            raise UnauthorizedAccessException("User associated with token no longer exists.")

        new_access_token = create_access_token(
            subject=str(user.id),
            claims={"email": user.email},
        )
        new_refresh_token = create_refresh_token(subject=str(user.id))

        return TokenResponse(
            access_token=new_access_token,
            refresh_token=new_refresh_token,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )

    async def get_current_user(self, user_id: uuid.UUID) -> User | None:
        return await self.user_repo.get_by_id(user_id)
