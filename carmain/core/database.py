from asyncio import current_task
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    create_async_engine,
    async_sessionmaker,
    AsyncSession,
    async_scoped_session,
)
from sqlalchemy.orm import DeclarativeBase

from carmain.core.config import get_settings

# from sqlalchemy import event
# from loguru import logger

import os

settings = get_settings()

# Use DATABASE_URL from environment if available (for production)
database_url = os.getenv("DATABASE_URL")
if database_url:
    # Convert to async URL if needed
    if database_url.startswith("postgresql://"):
        database_url = database_url.replace("postgresql://", "postgresql+asyncpg://", 1)
    engine = create_async_engine(database_url, echo=True)
else:
    # Fallback to settings for local development
    engine = create_async_engine(
        f"postgresql+asyncpg://{settings.postgres_user}:{settings.postgres_password}@{settings.postgres_host}:{settings.postgres_port}/{settings.db_name}",
        echo=True
    )
async_session_maker = async_sessionmaker(
    engine, expire_on_commit=False, class_=AsyncSession, autoflush=False
)


# @event.listens_for(engine.sync_engine, "before_cursor_execute")
# def log_sql_statements(conn, cursor, statement, parameters, context, executemany):
#     logger.info(f"Executing: {statement} with parameters: {parameters}")


class Base(DeclarativeBase):
    pass


class SessionManager:
    def __init__(self) -> None:
        self.session_factory = async_scoped_session(
            async_session_maker, scopefunc=current_task
        )
        self.session = None

    async def __aenter__(self) -> None:
        self.session = self.session_factory()

    async def __aexit__(self, *args: object) -> None:
        await self.rollback()

    async def commit(self) -> None:
        if self.session:
            await self.session.commit()
            await self.session.close()
        self.session = None

    async def rollback(self) -> None:
        if self.session:
            await self.session.rollback()
            await self.session.close()
        self.session = None


session_manager = SessionManager()


# async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
#     session: AsyncSession = async_session_maker()
#     try:
#         yield session
#     except Exception:
#         await session.rollback()
#         raise
#     finally:
#         await session.close()


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    async with session_manager:
        session = session_manager.session
        if session is None:
            raise Exception("SessionManager is not initialized")
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            # Closing the session after use...
            await session.close()


# class Database:
#     def __init__(self, db_url: str) -> None:
#         self._engine = create_async_engine(db_url, echo=True)
#         self._session_factory = async_scoped_session(
#             async_sessionmaker(
#                 self._engine, expire_on_commit=False, class_=AsyncSession
#             )
#         )
#
#     async def session(self):
#         session: AsyncSession = self._session_factory()
#         try:
#             yield session
#         except Exception:
#             await session.rollback()
#             raise
#         finally:
#             await session.close()
