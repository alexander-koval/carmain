import datetime

import pytest

from fastapi_users.authentication.strategy import DatabaseStrategy, JWTStrategy
from fastapi_users.authentication import BearerTransport, CookieTransport, AuthenticationBackend

from carmain.core.backend import (
    get_jwt_strategy,
    get_database_strategy,
    get_user_manager,
    get_backends,
    bearer_transport,
    cookie_backend,
    jwt_backend,
    password_helper,
    UserManager,
)
from carmain.core.database import settings as db_settings


@pytest.mark.asyncio
async def test_get_jwt_strategy():
    strat = get_jwt_strategy()
    assert isinstance(strat, JWTStrategy)
    assert strat.secret == db_settings.secret_key
    assert strat.lifetime_seconds == 3600
    assert strat.algorithm == "HS256"


def test_get_database_strategy():
    class DummyDB:
        pass
    dummy = DummyDB()
    strat = get_database_strategy(dummy)
    assert isinstance(strat, DatabaseStrategy)
    expected = int(datetime.timedelta(days=30).total_seconds())
    assert strat.lifetime_seconds == expected
    assert strat.database is dummy


@pytest.mark.asyncio
async def test_get_user_manager():
    dummy_db = object()
    gen = get_user_manager(dummy_db)
    managers = [mgr async for mgr in gen]
    assert len(managers) == 1
    mgr = managers[0]
    assert isinstance(mgr, UserManager)
    assert mgr.user_db is dummy_db
    assert mgr.password_helper is password_helper


def test_backends_configuration():
    backends = get_backends()
    # Should return cookie first, then jwt
    assert backends == [cookie_backend, jwt_backend]
    # Names
    assert cookie_backend.name == "cookie_session"
    assert jwt_backend.name == "jwt_session"
    # Transports
    # jwt_backend uses bearer transport instance
    assert jwt_backend.transport is bearer_transport
    assert isinstance(jwt_backend.transport, BearerTransport)
    # cookie_backend uses cookie transport instance
    from carmain.core.backend import cookie_transport as ct_inst
    assert cookie_backend.transport is ct_inst
    assert isinstance(cookie_backend.transport, CookieTransport)
    # CookieTransport defaults from settings
    ct = cookie_backend.transport
    assert ct.cookie_name == "token"
    assert ct.cookie_max_age == 86400
    # HTTPONLY from settings
    assert ct.cookie_httponly is True
    assert hasattr(ct, 'cookie_samesite')
    # Backends are AuthenticationBackend instances
    assert isinstance(cookie_backend, AuthenticationBackend)
    assert isinstance(jwt_backend, AuthenticationBackend)