import uuid
import pytest

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from carmain.core.database import Base
from carmain.models.users import User
from carmain.repository.user_repository import UserRepository
from carmain.schemas.auth_schema import SignIn
from carmain.core.exceptions import NotFoundError, DuplicatedError


@pytest.fixture
async def session(tmp_path):
    db_file = tmp_path / "test.db"
    engine = create_async_engine(f"sqlite+aiosqlite:///{db_file}", echo=False)
    async_session = async_sessionmaker(engine, expire_on_commit=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with async_session() as session:
        yield session
    await engine.dispose()


@pytest.mark.asyncio
async def test_get_by_email_existing(session):
    repo = UserRepository(session)
    user = User(email="user@example.com", hashed_password="secret")
    session.add(user)
    await session.commit()

    signin = SignIn(email="user@example.com", password="irrelevant")
    found = await repo.get_by_email(signin)
    assert found is not None
    assert found.email == "user@example.com"


@pytest.mark.asyncio
async def test_get_by_email_missing(session):
    repo = UserRepository(session)
    signin = SignIn(email="missing@example.com", password="irrelevant")
    found = await repo.get_by_email(signin)
    assert found is None


@pytest.mark.asyncio
async def test_get_by_id_and_delete(session):
    repo = UserRepository(session)
    user = User(email="first@example.com", hashed_password="pwd")
    session.add(user)
    await session.commit()

    user_id = user.id
    found = await repo.get_by_id(user_id)
    assert found.id == user_id
    assert found.email == "first@example.com"

    with pytest.raises(NotFoundError):
        await repo.get_by_id(user_id + 1)

    deleted = await repo.delete_by_id(user_id)
    assert deleted.id == user_id

    with pytest.raises(NotFoundError):
        await repo.get_by_id(user_id)


@pytest.mark.asyncio
async def test_update_by_id(session):
    repo = UserRepository(session)
    user = User(email="update@example.com", hashed_password="pwd")
    session.add(user)
    await session.commit()

    user_id = user.id
    updated = await repo.update_by_id(user_id, {"email": "updated@example.com"})
    assert updated.email == "updated@example.com"
    found = await repo.get_by_id(user_id)
    assert found.email == "updated@example.com"

    with pytest.raises(NotFoundError):
        await repo.update_by_id(user_id + 100, {"email": "x@example.com"})


@pytest.mark.asyncio
async def test_create_duplicate(session):
    repo = UserRepository(session)
    user1 = User(email="dup@example.com", hashed_password="pwd1")
    created1 = await repo.create(user1)
    assert created1.id is not None

    user2 = User(email="dup@example.com", hashed_password="pwd2")
    with pytest.raises(DuplicatedError):
        await repo.create(user2)