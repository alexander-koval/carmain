import datetime
from typing import Optional, Any, Annotated

from fastapi import Depends
from fastapi_users import BaseUserManager, IntegerIDMixin, models
from fastapi_users.authentication import CookieTransport, AuthenticationBackend
from fastapi_users.authentication.strategy import DatabaseStrategy, AccessTokenDatabase
from fastapi_users.password import PasswordHelper
from fastapi_users_db_sqlalchemy import SQLAlchemyUserDatabase
from passlib.exc import UnknownHashError
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status
from starlette.requests import Request

from carmain.core import database
from carmain.models.auth import AccessToken, get_access_token_db, get_async_session
from carmain.models.users import User, get_user_db
from carmain.repository.user_repository import UserRepository
from carmain.schema.auth_schema import SignUp  # , SignInResponse
from carmain.services.base_service import BaseService


class UserManager(IntegerIDMixin, BaseUserManager[User, int]):
    reset_password_token_secret = database.settings.secret_key
    verification_token_secret = database.settings.secret_key

    async def on_after_register(
        self, user: models.UP, request: Optional[Request] = None
    ) -> None:
        return await super().on_after_register(user, request)

    async def on_after_forgot_password(
        self, user: models.UP, token: str, request: Optional[Request] = None
    ) -> None:
        return await super().on_after_forgot_password(user, token, request)

    async def on_after_request_verify(
        self, user: models.UP, token: str, request: Optional[Request] = None
    ) -> None:
        return await super().on_after_request_verify(user, token, request)


password_helper = PasswordHelper()
cookie_transport = CookieTransport(cookie_name="token", cookie_max_age=3600)


async def get_user_manager(
    user_db: Annotated[SQLAlchemyUserDatabase, Depends(get_user_db)]
):
    yield UserManager(user_db, password_helper)


def get_database_strategy(
    access_token_db: Annotated[
        AccessTokenDatabase[AccessToken], Depends(get_access_token_db)
    ]
) -> DatabaseStrategy:
    lifetime = int(datetime.timedelta(days=30).total_seconds())
    return DatabaseStrategy(
        database=access_token_db,
        lifetime_seconds=lifetime,
    )


class AuthService(BaseService):
    def __init__(
        self,
        user_repository: Annotated[UserRepository, Depends(UserRepository)],
        user_manager: Annotated[UserManager, Depends(get_user_manager)],
        strategy: Annotated[DatabaseStrategy, Depends(get_database_strategy)],
    ):
        self.user_repository = user_repository
        self.user_manager = user_manager
        self.auth_backend = AuthenticationBackend(
            name="db_session",
            transport=cookie_transport,
            get_strategy=get_database_strategy,
        )
        self.strategy = strategy
        super().__init__(user_repository)

    async def sign_in(self, user_info):
        user: User = await self.user_repository.get_by_email(user_info)
        try:
            password_verified = password_helper.password_hash.verify(
                user_info.password, user.hashed_password
            )
        except UnknownHashError:
            password_verified = False
        if not user or not password_verified or user.is_active is False:
            return None
        await self.auth_backend.login(self.strategy, user)
        return user

    async def sing_up(self, user_info: SignUp):
        user = User(
            **user_info.model_dump(exclude_none=True, exclude={"password"}),
            is_active=True,
            is_superuser=False,
        )
        user.hashed_password = self.user_manager.password_helper.hash(
            user_info.password
        )
        created_user = await self.user_repository.create(user)
        delattr(created_user, "hashed_password")
        return created_user

    async def create_access_token(self, user: User) -> AccessToken:
        user_token = self.user_manager.password_helper.generate()
        access_token = AccessToken(token=user_token, user_id=user.id)
        return access_token
