from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase

from carmain.config.config import get_settings

settings = get_settings()
engine = create_async_engine(f'sqlite+aiosqlite:///{settings.db_name}.db', echo=True)
async_session_maker = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


class Base(DeclarativeBase):
    pass
