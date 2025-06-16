import sys
import uuid
from datetime import date

import pytest
from fastapi import HTTPException
from sqlalchemy.exc import SQLAlchemyError

from carmain.models.records import ServiceRecord
from carmain.services.maintenance_service import MaintenanceService
from carmain.schemas.maintenance_schema import (
    MaintenanceItemStatus,
    ServiceRecordCreate,
    UserMaintenanceItemUpdate,
)


@pytest.fixture
async def mocked_repositories(user, vehicle, user_maintenance_items, mock_repository):
    """Фикстура для создания моков репозиториев для тестирования сервиса обслуживания"""
    # Мок для MaintenanceRepository
    maintenance_repo = mock_repository
    maintenance_repo.get_maintenance_items_requiring_service.return_value = [
        user_maintenance_items[0],  # Просроченный
        user_maintenance_items[3],  # Никогда не обслуживался
    ]
    maintenance_repo.get_user_maintenance_items.return_value = user_maintenance_items

    # Мок для VehicleRepository
    vehicle_repo = mock_repository
    vehicle_repo.get_vehicle.return_value = vehicle

    # Мок для UserMaintenanceRepository
    user_maintenance_repo = mock_repository
    
    # Мок для ServiceRecordRepository
    record_repo = mock_repository
    
    return {
        "maintenance_repo": maintenance_repo,
        "vehicle_repo": vehicle_repo,
        "user_maintenance_repo": user_maintenance_repo,
        "record_repo": record_repo
    }


@pytest.fixture
async def maintenance_service(user, mocked_repositories):
    """Фикстура для создания тестового экземпляра MaintenanceService"""
    return MaintenanceService(
        maintenance_repo=mocked_repositories["maintenance_repo"],
        user_maintenance_repo=mocked_repositories["user_maintenance_repo"],
        vehicle_repo=mocked_repositories["vehicle_repo"],
        record_repo=mocked_repositories["record_repo"],
        user=user
    )


@pytest.mark.asyncio
async def test_get_items_requiring_service_count(maintenance_service, vehicle):
    """Тестирование функции get_items_requiring_service_count"""
    count = await maintenance_service.get_items_requiring_service_count(vehicle.id)
    
    assert count == 2
    
    maintenance_service.maintenance_repository.get_maintenance_items_requiring_service.assert_called_once_with(
        maintenance_service.user.id, vehicle.id, 0, sys.maxsize
    )


@pytest.mark.asyncio
async def test_get_items_requiring_service_overdue(maintenance_service, vehicle, user_maintenance_items):
    """Тестирование функции get_items_requiring_service для элементов, требующих обслуживания"""
    maintenance_service.maintenance_repository.get_maintenance_items_requiring_service.return_value = [
        user_maintenance_items[0],
        user_maintenance_items[3],
    ]
    
    display_items, pagination = await maintenance_service.get_items_requiring_service(
        vehicle_id=vehicle.id,
        page=1,
        page_size=10,
        show_all=False
    )
    
    assert len(display_items) == 2
    
    assert display_items[0].status == MaintenanceItemStatus.OVERDUE
    assert display_items[1].status == MaintenanceItemStatus.NEVER_SERVICED
    
    assert pagination["current_page"] == 1
    assert pagination["total_pages"] == 1
    assert pagination["items_per_page"] == 10
    assert pagination["total_items"] == 2


@pytest.mark.asyncio
async def test_get_items_requiring_service_show_all(maintenance_service, vehicle, user_maintenance_items):
    """Тестирование функции get_items_requiring_service с параметром show_all=True"""
    maintenance_service.maintenance_repository.get_user_maintenance_items.return_value = user_maintenance_items
    
    display_items, pagination = await maintenance_service.get_items_requiring_service(
        vehicle_id=vehicle.id,
        page=1,
        page_size=10,
        show_all=True
    )
    
    assert len(display_items) == 4
    
    statuses = [item.status for item in display_items]
    assert MaintenanceItemStatus.OVERDUE in statuses
    assert MaintenanceItemStatus.OK in statuses
    assert MaintenanceItemStatus.NEVER_SERVICED in statuses
    
    assert pagination["current_page"] == 1
    assert pagination["total_pages"] == 1
    assert pagination["items_per_page"] == 10
    assert pagination["total_items"] == 4


@pytest.mark.asyncio
async def test_get_items_requiring_service_nonexistent_vehicle(maintenance_service):
    """Тестирование функции get_items_requiring_service с несуществующим vehicle_id"""
    maintenance_service.vehicle_repository.get_vehicle.return_value = None
    
    nonexistent_id = uuid.uuid4()
    display_items, pagination = await maintenance_service.get_items_requiring_service(
        vehicle_id=nonexistent_id,
        page=1,
        page_size=10,
        show_all=False
    )
    
    assert len(display_items) == 0
    
    assert pagination["current_page"] == 1
    assert pagination["total_pages"] == 0
    assert pagination["items_per_page"] == 10
    assert pagination["total_items"] == 0


@pytest.mark.asyncio
async def test_mark_item_as_serviced_success(maintenance_service, user_maintenance_items, user):
    """Тестирование успешного выполнения функции mark_item_as_serviced"""
    item = user_maintenance_items[0]
    item.user_id = user.id  # Устанавливаем user_id равным id текущего пользователя
    maintenance_service.user_maintenance_repository.get_by_id.return_value = item
    
    service_date = date.today()
    service_odometer = 55000
    service_record_create = ServiceRecordCreate(
        user_item_id=item.id,
        service_date=service_date,
        service_odometer=service_odometer,
        comment="Тестовое обслуживание"
    )
    
    updated_item = item
    updated_item.last_service_date = service_date
    updated_item.last_service_odometer = service_odometer
    maintenance_service.user_maintenance_repository.update_by_id.return_value = updated_item
    maintenance_service.user_maintenance_repository.get_by_id.side_effect = [item, updated_item]
    
    result = await maintenance_service.mark_item_as_serviced(service_record_create)
    
    maintenance_service.record_repository.create.assert_called_once()
    maintenance_service.user_maintenance_repository.update_by_id.assert_called_once()
    assert result.last_service_date == service_date
    assert result.last_service_odometer == service_odometer


@pytest.mark.asyncio
async def test_mark_item_as_serviced_with_empty_comment(maintenance_service, user_maintenance_items, user):
    """Тестирование функции mark_item_as_serviced с пустым комментарием"""
    item = user_maintenance_items[0]
    item.user_id = user.id  # Устанавливаем user_id равным id текущего пользователя
    maintenance_service.user_maintenance_repository.get_by_id.return_value = item
    
    service_date = date.today()
    service_odometer = 55000
    service_record_create = ServiceRecordCreate(
        user_item_id=item.id,
        service_date=service_date,
        service_odometer=service_odometer,
        comment=""
    )
    
    updated_item = item
    updated_item.last_service_date = service_date
    updated_item.last_service_odometer = service_odometer
    maintenance_service.user_maintenance_repository.update_by_id.return_value = updated_item
    maintenance_service.user_maintenance_repository.get_by_id.side_effect = [item, updated_item]
    
    result = await maintenance_service.mark_item_as_serviced(service_record_create)
    
    called_args = maintenance_service.record_repository.create.call_args[0][0]
    expected_comment = f"Обслуживание выполнено {service_date.strftime('%d.%m.%Y')}"
    assert called_args.comment == expected_comment
    assert result.last_service_date == service_date
    assert result.last_service_odometer == service_odometer


@pytest.mark.asyncio
async def test_mark_item_as_serviced_without_odometer(maintenance_service, user_maintenance_items, vehicle, user):
    """Тестирование функции mark_item_as_serviced без указания пробега"""
    item = user_maintenance_items[0]
    item.user_id = user.id  # Устанавливаем user_id равным id текущего пользователя
    item.vehicle = vehicle
    maintenance_service.user_maintenance_repository.get_by_id.return_value = item
    
    service_date = date.today()
    # Передаем 0 вместо None, а в тесте проверяем, что функция использует odometer из vehicle
    service_record_create = ServiceRecordCreate(
        user_item_id=item.id,
        service_date=service_date,
        service_odometer=0,  # Заменяем None на 0, чтобы пройти валидацию
        comment="Тестовое обслуживание"
    )
    
    updated_item = item
    updated_item.last_service_date = service_date
    updated_item.last_service_odometer = vehicle.odometer
    maintenance_service.user_maintenance_repository.update_by_id.return_value = updated_item
    maintenance_service.user_maintenance_repository.get_by_id.side_effect = [item, updated_item]
    
    result = await maintenance_service.mark_item_as_serviced(service_record_create)
    
    called_args = maintenance_service.record_repository.create.call_args[0][0]
    assert called_args.service_odometer == vehicle.odometer
    assert result.last_service_date == service_date
    assert result.last_service_odometer == vehicle.odometer


@pytest.mark.asyncio
async def test_mark_item_as_serviced_item_not_found(maintenance_service):
    """Тестирование функции mark_item_as_serviced когда элемент не найден"""
    maintenance_service.user_maintenance_repository.get_by_id.return_value = None
    
    service_record_create = ServiceRecordCreate(
        user_item_id=uuid.uuid4(),
        service_date=date.today(),
        service_odometer=55000,
        comment="Тестовое обслуживание"
    )
    
    with pytest.raises(HTTPException) as excinfo:
        await maintenance_service.mark_item_as_serviced(service_record_create)
    
    assert excinfo.value.status_code == 404
    assert "Элемент обслуживания не найден" in excinfo.value.detail


@pytest.mark.asyncio
async def test_mark_item_as_serviced_wrong_user(maintenance_service, user_maintenance_items):
    """Тестирование функции mark_item_as_serviced с неправильным пользователем"""
    item = user_maintenance_items[0]
    item.user_id = uuid.uuid4()  # Установка другого user_id, не совпадающего с текущим пользователем
    maintenance_service.user_maintenance_repository.get_by_id.return_value = item
    
    service_record_create = ServiceRecordCreate(
        user_item_id=item.id,
        service_date=date.today(),
        service_odometer=55000,
        comment="Тестовое обслуживание"
    )
    
    with pytest.raises(HTTPException) as excinfo:
        await maintenance_service.mark_item_as_serviced(service_record_create)
    
    assert excinfo.value.status_code == 404
    assert "Элемент обслуживания не найден" in excinfo.value.detail


@pytest.mark.asyncio
async def test_create_maintenance_item(maintenance_service):
    """Тестирование функции create_maintenance_item"""
    item_data = {
        "name": "Тестовый элемент обслуживания",
        "default_interval": 15000
    }
    
    expected_item = maintenance_service.maintenance_repository.create.return_value
    
    result = await maintenance_service.create_maintenance_item(item_data)
    
    maintenance_service.maintenance_repository.create.assert_called_once()
    assert result == expected_item


@pytest.mark.asyncio
async def test_create_user_maintenance_item(maintenance_service):
    """Тестирование функции create_user_maintenance_item"""
    item_data = {
        "item_id": uuid.uuid4(),
        "vehicle_id": uuid.uuid4(),
        "custom_interval": 12000
    }
    
    expected_item = maintenance_service.user_maintenance_repository.create.return_value
    
    result = await maintenance_service.create_user_maintenance_item(item_data)
    
    maintenance_service.user_maintenance_repository.create.assert_called_once()
    assert result == expected_item


@pytest.mark.asyncio
async def test_update_user_maintenance_item(maintenance_service):
    """Тестирование функции update_user_maintenance_item"""
    item_id = uuid.uuid4()
    update_schema = UserMaintenanceItemUpdate(
        user_item_id=item_id,
        custom_interval=20000,
        last_service_odometer=45000,
        last_service_date=date.today()
    )
    
    expected_updated_item = maintenance_service.user_maintenance_repository.update_by_id.return_value
    
    result = await maintenance_service.update_user_maintenance_item(item_id, update_schema)
    
    maintenance_service.user_maintenance_repository.update_by_id.assert_called_once()
    assert result == expected_updated_item


@pytest.mark.asyncio
async def test_delete_user_maintenance_item_success(maintenance_service):
    """Тестирование успешного удаления пользовательского элемента обслуживания"""
    item_id = uuid.uuid4()
    maintenance_service.user_maintenance_repository.delete_by_id.return_value = True
    
    result = await maintenance_service.delete_user_maintenance_item(item_id)
    
    maintenance_service.user_maintenance_repository.delete_by_id.assert_called_once_with(item_id)
    assert result is True


@pytest.mark.asyncio
async def test_delete_user_maintenance_item_failure(maintenance_service):
    """Тестирование неудачного удаления пользовательского элемента обслуживания"""
    item_id = uuid.uuid4()
    maintenance_service.user_maintenance_repository.delete_by_id.side_effect = SQLAlchemyError("DB Error")
    
    result = await maintenance_service.delete_user_maintenance_item(item_id)
    
    maintenance_service.user_maintenance_repository.delete_by_id.assert_called_once_with(item_id)
    assert result is False


@pytest.mark.asyncio
async def test_get_maintenance_items(maintenance_service, maintenance_items):
    """Тестирование функции get_maintenance_items"""
    maintenance_service.maintenance_repository.get_maintenance_items.return_value = maintenance_items
    
    result = await maintenance_service.get_maintenance_items(skip=0, limit=10)
    
    maintenance_service.maintenance_repository.get_maintenance_items.assert_called_once_with(0, 10)
    assert result == maintenance_items


@pytest.mark.asyncio
async def test_get_maintenance_item(maintenance_service, maintenance_items):
    """Тестирование функции get_maintenance_item"""
    item_id = uuid.uuid4()
    maintenance_service.maintenance_repository.get_maintenance_item.return_value = maintenance_items[0]
    
    result = await maintenance_service.get_maintenance_item(item_id)
    
    maintenance_service.maintenance_repository.get_maintenance_item.assert_called_once_with(item_id)
    assert result == maintenance_items[0]


@pytest.mark.asyncio
async def test_get_user_vehicles(maintenance_service, vehicle):
    """Тестирование функции get_user_vehicles"""
    vehicles = [vehicle]
    maintenance_service.vehicle_repository.get_user_vehicles.return_value = vehicles
    
    result = await maintenance_service.get_user_vehicles()
    
    maintenance_service.vehicle_repository.get_user_vehicles.assert_called_once_with(maintenance_service.user.id)
    assert result == vehicles


@pytest.mark.asyncio
async def test_get_service_records(maintenance_service):
    """Тестирование функции get_service_records"""
    user_item_id = uuid.uuid4()
    service_records = [
        ServiceRecord(
            id=uuid.uuid4(),
            user_item_id=user_item_id,
            service_date=date.today(),
            service_odometer=50000,
            comment="Тестовая запись"
        )
    ]
    maintenance_service.record_repository.get_by_user_item_id.return_value = service_records
    
    result = await maintenance_service.get_service_records(user_item_id)
    
    maintenance_service.record_repository.get_by_user_item_id.assert_called_once_with(user_item_id)
    assert result == service_records