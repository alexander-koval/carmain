from typing import Annotated

from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from carmain.core.database import get_async_session
from carmain.models.users import User
from carmain.repository.base_repository import BaseRepository
from carmain.schema.auth_schema import SignIn


class UserRepository(BaseRepository):
    def __init__(
        self,
        session: Annotated[AsyncSession, Depends(get_async_session)],
    ) -> None:
        super().__init__(User, session)

    async def get_by_email(self, user_info: SignIn) -> User:
        obj = await self.session.scalar(
            select(User).where(User.email == user_info.email)  # type: ignore
        )
        return obj
