from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from carmain.core.db import get_async_session
from carmain.models.users import User
from carmain.repository.base_repository import BaseRepository


class UserRepository(BaseRepository):
    def __init__(
        self, session: Annotated[AsyncSession, Depends(get_async_session)]
    ) -> None:
        super().__init__(User, session)
