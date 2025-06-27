from sqladmin.authentication import AuthenticationBackend
from sqlalchemy import select
from sqlalchemy.orm import joinedload
from starlette.requests import Request
from starlette.responses import RedirectResponse, Response

from carmain.core import backend
from carmain.core.database import async_session_maker
from carmain.models.auth import AccessToken


class AdminAuthBackend(AuthenticationBackend):
    """Authentication backend for SQLAdmin, only superusers allowed."""

    def __init__(self, secret_key: str):
        super().__init__(secret_key)

    async def login(self, request: Request) -> Response:
        return RedirectResponse(url="/auth/login", status_code=302)

    async def logout(self, request: Request) -> Response:
        return RedirectResponse(url="/auth/logout", status_code=302)

    async def authenticate(self, request: Request) -> bool:
        token = await backend.cookie_transport.scheme(request)
        if not token:
            token = await backend.bearer_transport.scheme(request)

        if not token:
            return False

        async with async_session_maker() as session:
            query = (
                select(AccessToken)
                .where(AccessToken.token == token)
                .options(joinedload(AccessToken.user))
            )
            db_token = await session.scalar(query)

            if db_token and db_token.user:
                return db_token.user.is_superuser

        return False
