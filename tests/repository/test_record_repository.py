import uuid
from datetime import datetime, timedelta

import pytest

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from carmain.core.database import Base
from carmain.models.records import ServiceRecord
from carmain.repository.record_repository import ServiceRecordRepository
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
async def test_get_by_user_item_id_and_all(session):
    repo = ServiceRecordRepository(session)
    uid1 = uuid.uuid4()
    uid2 = uuid.uuid4()
    sr1 = ServiceRecord(
        user_item_id=uid1,
        service_date=datetime.utcnow() - timedelta(days=2),
        service_odometer=100,
        comment="Rec1",
    )
    sr2 = ServiceRecord(
        user_item_id=uid1,
        service_date=datetime.utcnow() - timedelta(days=1),
        service_odometer=200,
        comment="Rec2",
    )
    sr3 = ServiceRecord(
        user_item_id=uid2,
        service_date=datetime.utcnow(),
        service_odometer=300,
        comment="Rec3",
    )
    session.add_all([sr1, sr2, sr3])
    await session.commit()

    all_records = await repo.all()
    assert len(all_records) == 3

    recs_uid1 = await repo.get_by_user_item_id(uid1)
    assert len(recs_uid1) == 2
    comments = {r.comment for r in recs_uid1}
    assert comments == {"Rec1", "Rec2"}

    recs_skip = await repo.get_by_user_item_id(uid1, skip=1, limit=1)
    assert len(recs_skip) == len(recs_uid1)
    assert {r.comment for r in recs_skip} == comments

    eager_recs = await repo.get_by_user_item_id(uid1, eager=True)
    assert len(eager_recs) == 2

    no_recs = await repo.get_by_user_item_id(uuid.uuid4())
    assert no_recs == []


@pytest.mark.asyncio
async def test_crud_operations(session):
    repo = ServiceRecordRepository(session)
    uid = uuid.uuid4()
    sr = ServiceRecord(
        user_item_id=uid,
        service_date=datetime.utcnow(),
        service_odometer=123,
        comment="CreateTest",
    )
    created = await repo.create(sr)
    assert created.id is not None

    found = await repo.get_by_id(created.id)
    assert found.comment == "CreateTest"

    with pytest.raises(NotFoundError):
        await repo.get_by_id(str(uuid.uuid4()))

    updated = await repo.update_by_id(created.id, {"comment": "Updated"})
    assert updated.comment == "Updated"
    verify = await repo.get_by_id(created.id)
    assert verify.comment == "Updated"

    deleted = await repo.delete_by_id(created.id)
    assert deleted.id == created.id
    with pytest.raises(NotFoundError):
        await repo.get_by_id(created.id)
