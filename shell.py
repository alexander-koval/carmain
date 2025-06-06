from typing import Generator

from IPython import embed
from fastapi import Depends
from fastapi_users_db_sqlalchemy import SQLAlchemyUserDatabase

from carmain.core.database import Base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, update, insert, delete  # noqa
from carmain.core.config import get_settings
from carmain.models.auth import *
from carmain.models.users import *
from carmain.models.items import *
from carmain.models.vehicles import *
from carmain.models.records import *

settings = get_settings()
# print(settings)
#engine = create_engine(f"sqlite:///{settings.db_name}.db", echo=True)
engine = create_engine(f"postgresql+psycopg2://{settings.postgres_user}:{settings.postgres_password}@{settings.postgres_host}:{settings.postgres_port}/{settings.db_name}")
Session = sessionmaker(engine)


def get_session() -> Generator:
    with Session() as session:
        yield session


def get_user_db(session=Depends(get_session)):
    yield SQLAlchemyUserDatabase(session, User)


banner = "Additional imports:\n"


for clazz in Base.registry._class_registry.values():
    if hasattr(clazz, "__tablename__"):
        globals()[clazz.__name__] = clazz
        import_string = f"from {clazz.__module__} import {clazz.__name__}\n"
        banner = banner + import_string

embed(colors="neutral", banner2=banner)


# Example
from carmain.models.users import User

with Session() as session:
    result = session.scalars(select(User))
    for user in result.all():
        print(user)
