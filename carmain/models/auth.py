from fastapi import Depends
from fastapi_users_db_sqlalchemy.access_token import (
    SQLAlchemyBaseAccessTokenTable,
    SQLAlchemyAccessTokenDatabase,
)
from sqlalchemy import Integer, ForeignKey, JSON
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, relationship, mapped_column, registry

from carmain.core.database import Base, get_async_session
from carmain.models.users import User


class AccessToken(SQLAlchemyBaseAccessTokenTable, Base):
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("user.id"))
    data: Mapped[dict] = mapped_column(JSON, nullable=True)
    user: Mapped[User] = relationship(back_populates="sessions")


async def get_access_token_db(session: AsyncSession = Depends(get_async_session)):
    yield SQLAlchemyAccessTokenDatabase(session, AccessToken)
