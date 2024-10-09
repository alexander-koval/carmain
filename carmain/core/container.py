from dependency_injector import containers, providers

from carmain.core.db import Database, settings


class Container(containers.DeclarativeContainer):
    wiring_config = containers.WiringConfiguration(
        # modules=[
        #     "carmain.api.v1.endpoints.auth",
        #     "carmain.api.v1.endpoints.user",
        # ]
    )

    db = providers.Singleton(
        Database, db_url=f"sqlite+aiosqlite:///{settings.db_name}.db"
    )
