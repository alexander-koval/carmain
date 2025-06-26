import uuid

import pytest

from carmain.models.vehicles import Vehicle
from carmain.schemas.vehicle_schema import VehicleSchema
from carmain.services.vehicle_service import VehicleService


@pytest.fixture
def vehicle_service(mock_repository, user):
    return VehicleService(repository=mock_repository, user=user)


@pytest.mark.asyncio
async def test_get_by_id_calls_repository(mock_repository, vehicle_service):
    obj_id = uuid.uuid4()
    fake_vehicle = object()
    mock_repository.get_by_id.return_value = fake_vehicle
    result = await vehicle_service.get_by_id(obj_id)
    assert result is fake_vehicle
    mock_repository.get_by_id.assert_awaited_once_with(obj_id)


@pytest.mark.asyncio
async def test_add_sets_user_id_and_calls_create(mock_repository, vehicle_service, user):
    created_vehicle = object()
    mock_repository.create.return_value = created_vehicle
    schema = VehicleSchema(brand="Brand", model="Model", year=2021, odometer=15000)
    result = await vehicle_service.add(schema)
    assert result is created_vehicle
    assert mock_repository.create.call_count == 1
    created_arg = mock_repository.create.call_args.args[0]
    assert isinstance(created_arg, Vehicle)
    assert created_arg.brand == "Brand"
    assert created_arg.model == "Model"
    assert created_arg.year == 2021
    assert created_arg.odometer == 15000
    assert created_arg.user_id == user.id


@pytest.mark.asyncio
async def test_patch_calls_update_by_id_with_correct_data(mock_repository, vehicle_service):
    obj_id = uuid.uuid4()
    updated_vehicle = object()
    mock_repository.update_by_id.return_value = updated_vehicle
    schema = VehicleSchema(brand="B", model="M", year=2010, odometer=5000)
    result = await vehicle_service.patch(obj_id, schema)
    assert result is updated_vehicle
    expected_data = {"brand": "B", "model": "M", "year": 2010, "odometer": 5000}
    mock_repository.update_by_id.assert_awaited_once_with(obj_id, expected_data)


@pytest.mark.asyncio
async def test_remove_by_id_calls_delete_by_id(mock_repository, vehicle_service):
    obj_id = uuid.uuid4()
    deleted_vehicle = object()
    mock_repository.delete_by_id.return_value = deleted_vehicle
    result = await vehicle_service.remove_by_id(obj_id)
    assert result is deleted_vehicle
    mock_repository.delete_by_id.assert_awaited_once_with(obj_id)


@pytest.mark.asyncio
async def test_all_returns_all_vehicles(mock_repository, vehicle_service):
    vehicles = [object(), object()]
    mock_repository.all.return_value = vehicles
    result = await vehicle_service.all()
    assert result == vehicles
    mock_repository.all.assert_awaited_once()


@pytest.mark.asyncio
async def test_get_user_vehicles_calls_get_by_user_id(mock_repository, vehicle_service, user):
    vehicles = [object(), object()]
    mock_repository.get_by_user_id.return_value = vehicles
    result = await vehicle_service.get_user_vehicles()
    assert result == vehicles
    mock_repository.get_by_user_id.assert_awaited_once_with(user.id)