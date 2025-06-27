import uuid
from datetime import datetime, timedelta

import pytest

from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.ext.asyncio import async_sessionmaker

from carmain.core.database import Base
from carmain.repository.maintenance_repository import (
    MaintenanceRepository,
    UserMaintenanceRepository,
)
from carmain.models.items import MaintenanceItem, UserMaintenanceItem
from carmain.models.records import ServiceRecord
from carmain.models.vehicles import Vehicle
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
async def test_get_maintenance_items_and_item(session):
    repo = MaintenanceRepository(session)
    item1 = MaintenanceItem(name="Oil Change", default_interval=5000)
    item2 = MaintenanceItem(name="Tire Rotation", default_interval=10000)
    session.add_all([item1, item2])
    await session.commit()

    items = await repo.get_maintenance_items()
    assert len(items) == 2
    names = {it.name for it in items}
    assert names == {"Oil Change", "Tire Rotation"}

    found = await repo.get_maintenance_item(item1.id)
    assert found is not None
    assert found.name == "Oil Change"

    missing = await repo.get_maintenance_item(uuid.uuid4())
    assert missing is None


@pytest.mark.asyncio
async def test_user_maintenance_items_and_count(session):
    repo = MaintenanceRepository(session)

    mitem = MaintenanceItem(name="Brake Check", default_interval=7000)
    session.add(mitem)
    await session.commit()

    user_id = 1
    vehicle_id = uuid.uuid4()
    umi1 = UserMaintenanceItem(
        user_id=user_id,
        item_id=mitem.id,
        vehicle_id=vehicle_id,
        custom_interval=None,
        last_service_odometer=None,
    )
    umi2 = UserMaintenanceItem(
        user_id=user_id,
        item_id=mitem.id,
        vehicle_id=vehicle_id,
        custom_interval=8000,
        last_service_odometer=1000,
    )
    session.add_all([umi1, umi2])
    await session.commit()

    all_items = await repo.get_user_maintenance_items(user_id)
    assert len(all_items) == 2

    filt = await repo.get_user_maintenance_items(user_id, vehicle_id=vehicle_id)
    assert len(filt) == 2

    count = await repo.get_vehicle_maintenance_items_count(user_id, vehicle_id)
    assert count == 2

    one = await repo.get_user_maintenance_item(umi1.id)
    assert one is not None
    assert one.id == umi1.id

    missing = await repo.get_user_maintenance_item(uuid.uuid4())
    assert missing is None

    deleted = await repo.delete_user_maintenance_item(umi1.id)
    assert deleted is True

    deleted_again = await repo.delete_user_maintenance_item(umi1.id)
    assert deleted_again is False


@pytest.mark.asyncio
async def test_get_service_records(session):
    repo = MaintenanceRepository(session)
    um_id = uuid.uuid4()
    sr1 = ServiceRecord(
        user_item_id=um_id,
        service_date=datetime.utcnow() - timedelta(days=1),
        service_odometer=1200,
        comment="First",
    )
    sr2 = ServiceRecord(
        user_item_id=um_id,
        service_date=datetime.utcnow(),
        service_odometer=1300,
        comment="Second",
    )
    session.add_all([sr1, sr2])
    await session.commit()

    records = await repo.get_service_records(um_id)
    assert len(records) == 2

    assert records[0].comment == "Second"
    assert records[1].comment == "First"


@pytest.mark.asyncio
async def test_get_maintenance_items_requiring_service(session):
    user_id = 2

    mitem = MaintenanceItem(name="Engine Check", default_interval=5000)
    session.add(mitem)

    vehicle = Vehicle(
        user_id=user_id, brand="Test", model="X", year=2020, odometer=6000
    )
    session.add(vehicle)
    await session.commit()

    vehicle_id = vehicle.id

    umi_never = UserMaintenanceItem(
        user_id=user_id,
        item_id=mitem.id,
        vehicle_id=vehicle_id,
        custom_interval=None,
        last_service_odometer=None,
    )
    umi_ok = UserMaintenanceItem(
        user_id=user_id,
        item_id=mitem.id,
        vehicle_id=vehicle_id,
        custom_interval=None,
        last_service_odometer=2000,  # diff = 4000 < 5000
    )
    umi_due = UserMaintenanceItem(
        user_id=user_id,
        item_id=mitem.id,
        vehicle_id=vehicle_id,
        custom_interval=None,
        last_service_odometer=1000,  # diff = 5000 == interval, due
    )
    session.add_all([umi_never, umi_ok, umi_due])
    await session.commit()

    repo = MaintenanceRepository(session)
    due_items = await repo.get_maintenance_items_requiring_service(user_id, vehicle_id)

    ids = {item.id for item in due_items}
    assert umi_never.id in ids
    assert umi_due.id in ids
    assert umi_ok.id not in ids


@pytest.mark.asyncio
async def test_user_repository_getters(session):
    um_repo = UserMaintenanceRepository(session)
    vehicle_a = uuid.uuid4()
    vehicle_b = uuid.uuid4()
    umi_a1 = UserMaintenanceItem(
        user_id=3,
        item_id=uuid.uuid4(),
        vehicle_id=vehicle_a,
        custom_interval=None,
        last_service_odometer=None,
    )
    umi_a2 = UserMaintenanceItem(
        user_id=3,
        item_id=uuid.uuid4(),
        vehicle_id=vehicle_a,
        custom_interval=None,
        last_service_odometer=None,
    )
    umi_b = UserMaintenanceItem(
        user_id=3,
        item_id=uuid.uuid4(),
        vehicle_id=vehicle_b,
        custom_interval=None,
        last_service_odometer=None,
    )
    session.add_all([umi_a1, umi_a2, umi_b])
    await session.commit()

    a_items = await um_repo.get_by_vehicle(vehicle_a)
    assert len(a_items) == 2

    empty = await um_repo.get_by_vehicle(uuid.uuid4())
    assert empty == []

    found = await um_repo.get_by_item_id(umi_b.item_id)
    assert found.id == umi_b.id

    with pytest.raises(NotFoundError):
        await um_repo.get_by_item_id(uuid.uuid4())
