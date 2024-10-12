import datetime
from typing import Optional, Annotated

from fastapi import Request, Depends
from fastapi_users import IntegerIDMixin, BaseUserManager, models
from fastapi_users.authentication import CookieTransport, AuthenticationBackend
from fastapi_users.authentication.strategy import AccessTokenDatabase, DatabaseStrategy
from fastapi_users.password import PasswordHelper
from fastapi_users_db_sqlalchemy import SQLAlchemyUserDatabase

from carmain.core import db
from carmain.models.auth import AccessToken, get_access_token_db
from carmain.models.users import User, get_user_db


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


async def get_user_manager(
    user_db: Annotated[SQLAlchemyUserDatabase, Depends(get_user_db)]
):
    yield UserManager(user_db, password_helper)


class UserManager(IntegerIDMixin, BaseUserManager[User, int]):
    reset_password_token_secret = db.settings.secret_key
    verification_token_secret = db.settings.secret_key

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
auth_backend = AuthenticationBackend(
            name="db_session",
            transport=cookie_transport,
            get_strategy=get_database_strategy,
        )