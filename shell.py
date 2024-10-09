from IPython import embed
from carmain.backend.db import Base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, update, insert, delete  # noqa
from carmain.config.config import get_settings

settings = get_settings()
# print(settings)
engine = create_engine(f'sqlite:///{settings.db_name}.db', echo=True)
Session = sessionmaker(engine)

banner = "Additional imports:\n"
#from carmain.main import app

for clazz in Base.registry._class_registry.values():
    if hasattr(clazz, "__tablename__"):
        globals()[clazz.__name__] = clazz
        import_string = f"from {clazz.__module__} import {clazz.__name__}\n"
        banner = banner + import_string

embed(colors="neutral", banner2=banner)


# Example
# from carmain.models.users import User
# with Session() as session:
#     result = session.scalars(select(User).where(Review.is_active == True))
#     for user in result.all():
#        print(user)