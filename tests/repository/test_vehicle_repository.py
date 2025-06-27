import uuid

import pytest

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from carmain.core.database import Base
from carmain.models.vehicles import Vehicle
from carmain.repository.vehicle_repository import VehicleRepository
from carmain.core.exceptions import NotFoundError


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
async def test_get_by_user_id_and_user_vehicles(session):
    repo = VehicleRepository(session)
    empty = await repo.get_by_user_id(1)
    assert empty == []

    v1 = Vehicle(user_id=1, brand="A", model="X", year=2021, odometer=100)
    v2 = Vehicle(user_id=1, brand="B", model="Y", year=2020, odometer=200)
    v3 = Vehicle(user_id=2, brand="C", model="Z", year=2019, odometer=300)
    session.add_all([v1, v2, v3])
    await session.commit()

    user1 = await repo.get_by_user_id(1)
    assert len(user1) == 2
    ids = {veh.id for veh in user1}
    assert ids == {v1.id, v2.id}

    alias = await repo.get_user_vehicles(1)
    assert {veh.id for veh in alias} == ids


@pytest.mark.asyncio
async def test_get_vehicle(session):
    repo = VehicleRepository(session)
    v = Vehicle(user_id=3, brand="D", model="W", year=2022, odometer=400)
    session.add(v)
    await session.commit()

    found = await repo.get_vehicle(v.id)
    assert found.id == v.id
    assert found.brand == "D"

    with pytest.raises(NotFoundError):
        await repo.get_vehicle(uuid.uuid4())
