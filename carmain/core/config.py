from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict

# from loguru import logger
# import sys
#
#
# logger.remove()
# logger.add(sys.stdout, format="{time} {level} {message}", level="INFO")


class Settings(BaseSettings):
    app_name: str = "Car Maintenance"
    admin_email: str
    items_per_user: int = 50
    secret_key: str
    db_name: str
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_user: str
    postgres_password: str

    model_config = SettingsConfigDict(env_file=".env")


@lru_cache
def get_settings():
    return Settings()
