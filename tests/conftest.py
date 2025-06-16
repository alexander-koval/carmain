"""
Глобальные фикстуры для тестов
"""
import uuid
from datetime import date, timedelta
from unittest.mock import AsyncMock

import pytest

from carmain.models.items import MaintenanceItem, UserMaintenanceItem
from carmain.models.vehicles import Vehicle
from carmain.models.users import User


@pytest.fixture
def user():
    """Фикстура для создания тестового пользователя"""
    return User(id=uuid.uuid4(), email="test@example.com")


@pytest.fixture
def vehicle():
    """Фикстура для создания тестового автомобиля"""
    return Vehicle(
        id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        brand="Toyota",
        model="Corolla",
        year=2018,
        odometer=50000,
    )


@pytest.fixture
def maintenance_items():
    """Фикстура для создания тестовых элементов обслуживания"""
    return [
        MaintenanceItem(
            id=uuid.uuid4(),
            name="Замена масла",
            default_interval=10000
        ),
        MaintenanceItem(
            id=uuid.uuid4(),
            name="Замена тормозных колодок",
            default_interval=30000
        ),
        MaintenanceItem(
            id=uuid.uuid4(),
            name="Замена воздушного фильтра",
            default_interval=20000
        ),
    ]


@pytest.fixture
def user_maintenance_items(maintenance_items, vehicle):
    """Фикстура для создания тестовых пользовательских элементов обслуживания"""
    today = date.today()
    last_month = today - timedelta(days=30)
    
    return [
        UserMaintenanceItem(
            id=uuid.uuid4(),
            user_id=vehicle.user_id,
            maintenance_item=maintenance_items[0],
            vehicle=vehicle,
            custom_interval=None,
            last_service_odometer=35000,
            last_service_date=last_month,
        ),
        UserMaintenanceItem(
            id=uuid.uuid4(),
            user_id=vehicle.user_id,
            maintenance_item=maintenance_items[1],
            vehicle=vehicle,
            custom_interval=None,
            last_service_odometer=23000,
            last_service_date=last_month,
        ),
        UserMaintenanceItem(
            id=uuid.uuid4(),
            user_id=vehicle.user_id,
            maintenance_item=maintenance_items[2],
            vehicle=vehicle,
            custom_interval=None,
            last_service_odometer=45000,
            last_service_date=today,
        ),
        UserMaintenanceItem(
            id=uuid.uuid4(),
            user_id=vehicle.user_id,
            maintenance_item=maintenance_items[0],
            vehicle=vehicle,
            custom_interval=None,
            last_service_odometer=None,
            last_service_date=None,
        ),
    ]


@pytest.fixture
def mock_repository():
    """Базовая фикстура для создания заглушки репозитория"""
    return AsyncMock()