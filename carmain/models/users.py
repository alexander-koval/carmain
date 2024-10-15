from fastapi import Depends
from fastapi_users_db_sqlalchemy import SQLAlchemyUserDatabase
from fastapi_users_db_sqlalchemy import SQLAlchemyBaseUserTable
from sqlalchemy import String, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from carmain.core.database import Base, get_async_session


class User(SQLAlchemyBaseUserTable, Base):
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    sessions: Mapped[list["AccessToken"]] = relationship(
        back_populates="user", lazy="joined"
    )


async def get_user_db(session=Depends(get_async_session)):
    yield SQLAlchemyUserDatabase(session, User)
