import pytest
import datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock
from passlib.exc import UnknownHashError

from carmain.services.auth_service import AuthService, get_database_strategy
from carmain.schemas.auth_schema import SignIn, SignUp
from carmain.models.users import User
from carmain.models.auth import AccessToken
from fastapi_users.authentication.strategy import DatabaseStrategy


@pytest.fixture
def fake_user_manager():
    class FakePasswordHelper:
        def hash(self, password):
            return f"hashed-{password}"

        def generate(self):
            return "token-123"

    class FakeUserManager:
        def __init__(self):
            self.password_helper = FakePasswordHelper()

    return FakeUserManager()


@pytest.fixture
def fake_strategy():
    return object()


@pytest.fixture
def auth_service(mock_repository, fake_user_manager, fake_strategy, monkeypatch):
    class FakeModulePH:
        def __init__(self):
            self.password_hash = self

        def verify(self, plain, hashed):
            return True

    fake_mod_ph = FakeModulePH()
    monkeypatch.setattr("carmain.services.auth_service.password_helper", fake_mod_ph)
    service = AuthService(
        user_repository=mock_repository,
        user_manager=fake_user_manager,
        strategy=fake_strategy,
    )
    service.auth_backend.login = AsyncMock()
    return service


def test_get_database_strategy_sets_properties():
    dummy_db = object()
    strategy = get_database_strategy(dummy_db)
    assert isinstance(strategy, DatabaseStrategy)
    assert strategy.database is dummy_db
    expected = int(datetime.timedelta(days=30).total_seconds())
    assert strategy.lifetime_seconds == expected


@pytest.mark.asyncio
async def test_sign_in_success(auth_service, mock_repository):
    user_info = SignIn(email="user@example.com", password="pass")
    fake_user = User(id=1, email="user@example.com")
    fake_user.hashed_password = "hashed"
    fake_user.is_active = True
    mock_repository.get_by_email.return_value = fake_user
    result = await auth_service.sign_in(user_info)
    assert result is fake_user
    mock_repository.get_by_email.assert_awaited_once_with(user_info)
    auth_service.auth_backend.login.assert_awaited_once_with(
        auth_service.strategy, fake_user
    )


@pytest.mark.asyncio
async def test_sign_in_wrong_password(auth_service, mock_repository, monkeypatch):
    import carmain.services.auth_service as auth_module

    user_info = SignIn(email="user@example.com", password="pass")
    fake_user = User(id=1, email="user@example.com")
    fake_user.hashed_password = "hashed"
    fake_user.is_active = True
    mock_repository.get_by_email.return_value = fake_user
    monkeypatch.setattr(
        auth_module.password_helper.password_hash,
        "verify",
        lambda plain, hashed: False,
        raising=False,
    )
    result = await auth_service.sign_in(user_info)
    assert result is None
    auth_service.auth_backend.login.assert_not_awaited()


@pytest.mark.asyncio
async def test_sign_in_unknown_hash(auth_service, mock_repository, monkeypatch):
    import carmain.services.auth_service as auth_module

    user_info = SignIn(email="user@example.com", password="pass")
    fake_user = User(id=1, email="user@example.com")
    fake_user.hashed_password = "hashed"
    fake_user.is_active = True
    mock_repository.get_by_email.return_value = fake_user

    def raise_unknown(*args, **kwargs):
        raise UnknownHashError()

    monkeypatch.setattr(
        auth_module.password_helper.password_hash,
        "verify",
        raise_unknown,
        raising=False,
    )
    result = await auth_service.sign_in(user_info)
    assert result is None
    auth_service.auth_backend.login.assert_not_awaited()


@pytest.mark.asyncio
async def test_sign_in_inactive_user(auth_service, mock_repository):
    user_info = SignIn(email="user@example.com", password="pass")
    fake_user = User(id=1, email="user@example.com")
    fake_user.hashed_password = "hashed"
    fake_user.is_active = False
    mock_repository.get_by_email.return_value = fake_user
    result = await auth_service.sign_in(user_info)
    assert result is None
    auth_service.auth_backend.login.assert_not_awaited()


@pytest.mark.asyncio
async def test_sing_up_creates_user_and_removes_hashed_password(
    auth_service, mock_repository
):
    mock_repository.create.side_effect = lambda u: u
    email = "new@example.com"
    password = "newpass"
    user_info = SignUp(email=email, password=password)
    result = await auth_service.sing_up(user_info)
    created_arg = mock_repository.create.call_args.args[0]
    assert isinstance(created_arg, User)
    assert created_arg.email == email
    assert created_arg.is_active is True
    assert created_arg.is_superuser is False
    assert result.hashed_password is None


@pytest.mark.asyncio
async def test_create_access_token_returns_token_with_user_id(auth_service):
    user = SimpleNamespace(id=42)
    result = await auth_service.create_access_token(user)
    assert isinstance(result, AccessToken)
    assert result.token == "token-123"
    assert result.user_id == 42
