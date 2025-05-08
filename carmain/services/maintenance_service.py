import uuid
from datetime import date, datetime
from typing import List, Optional, Dict, Any, Tuple, Annotated, Sequence, Coroutine

from fastapi import Depends
from pydantic import BaseModel
from sqlalchemy.exc import SQLAlchemyError

from carmain.models.items import MaintenanceItem, UserMaintenanceItem
from carmain.models.records import ServiceRecord
from carmain.models.vehicles import Vehicle
from carmain.models.users import User
from carmain.repository.maintenance_repository import (
    MaintenanceRepository,
    UserMaintenanceRepository,
)
from carmain.repository.record_repository import ServiceRecordRepository
from carmain.repository.vehicle_repository import VehicleRepository
from carmain.schemas.maintenance_schema import (
    MaintenanceItemStatus,
    MaintenanceItemType,
    MaintenanceItemDisplay,
)
from carmain.services.base_service import BaseService
from carmain.routers.v1.auth_router import current_active_verified_user


class MaintenanceService(BaseService):
    """Сервис для управления обслуживанием автомобилей"""

    def __init__(
        self,
        maintenance_repo: Annotated[MaintenanceRepository, Depends()],
        user_maintenance_repo: Annotated[UserMaintenanceRepository, Depends()],
        vehicle_repo: Annotated[VehicleRepository, Depends()],
        record_repo: Annotated[ServiceRecordRepository, Depends()],
        user: Annotated[User, Depends(current_active_verified_user)],
    ):
        self.maintenance_repository = maintenance_repo
        self.user_maintenance_repository = user_maintenance_repo
        self.vehicle_repository = vehicle_repo
        self.record_repository = record_repo
        self.user = user

    async def get_maintenance_items(
        self, skip: int = 0, limit: int = 10
    ) -> Sequence[MaintenanceItem]:
        """Получить список всех типов обслуживания"""
        return await self.maintenance_repository.get_maintenance_items(skip, limit)

    async def get_maintenance_item(
        self, item_id: uuid.UUID
    ) -> Optional[MaintenanceItem]:
        """Получить информацию о типе обслуживания по ID"""
        return await self.maintenance_repository.get_maintenance_item(item_id)

    async def create_maintenance_item(
        self, item_data: Dict[str, Any]
    ) -> MaintenanceItem:
        """Создать новый тип обслуживания"""
        db_item = MaintenanceItem(user_id=self.user.id, **item_data)
        return await self.maintenance_repository.create(db_item)

    async def get_user_vehicles(self) -> List[Vehicle]:
        """Получить все автомобили пользователя"""
        return await self.vehicle_repository.get_user_vehicles(self.user.id)

    async def get_vehicle(self, vehicle_id: uuid.UUID) -> Optional[Vehicle]:
        """Получить автомобиль по ID"""
        return await self.vehicle_repository.get_vehicle(vehicle_id)

    async def get_user_maintenance_items(
        self, vehicle_id: Optional[uuid.UUID] = None, skip: int = 0, limit: int = 10
    ) -> Sequence[UserMaintenanceItem]:
        """Получить список элементов обслуживания пользователя"""
        return await self.user_maintenance_repository.get_by_vehicle(
            vehicle_id, skip, limit, eager=True
        )

    async def get_user_maintenance_item(
        self, item_id: uuid.UUID
    ) -> Optional[UserMaintenanceItem]:
        """Получить элемент обслуживания пользователя по ID"""
        return await self.user_maintenance_repository.get_by_id(item_id, eager=True)

    async def create_user_maintenance_item(
        self, item_data: Dict[str, Any]
    ) -> UserMaintenanceItem:
        """Создать элемент обслуживания для пользователя"""
        db_item = UserMaintenanceItem(user_id=self.user.id, **item_data)
        return await self.user_maintenance_repository.create(db_item)

    async def update_user_maintenance_item(
        self, item_id: uuid.UUID, schema: BaseModel
    ) -> Optional[UserMaintenanceItem]:
        """Обновить элемент обслуживания пользователя"""
        update_data: dict[str, Any] = schema.model_dump(
            exclude_unset=True, exclude_defaults=True, exclude_none=True
        )
        return await self.user_maintenance_repository.update_by_id(item_id, update_data)

    async def delete_user_maintenance_item(self, item_id: uuid.UUID) -> bool:
        """Удалить элемент обслуживания пользователя"""
        try:
            return await self.user_maintenance_repository.delete_by_id(item_id)
        except SQLAlchemyError:
            return False

    async def get_service_records(
        self, user_item_id: uuid.UUID
    ) -> Sequence[ServiceRecord]:
        """Получить историю обслуживания для конкретного элемента"""
        return await self.record_repository.get_by_user_item_id(user_item_id)

    async def create_service_record(self, record: BaseModel) -> ServiceRecord:
        """Создать запись об обслуживании"""
        record_data = record.model_dump(exclude_unset=True)
        db_item = ServiceRecord(**record_data)
        return await self.record_repository.create(db_item)

    async def mark_item_as_serviced(
        self,
        item_id: uuid.UUID,
        service_date: date,
        service_odometer: Optional[int] = None,
        comment: Optional[str] = None,
        photo_path: Optional[str] = None,
    ) -> Optional[ServiceRecord]:
        """Отметить элемент как обслуженный"""
        # Проверяем, что элемент принадлежит пользователю
        item = await self.maintenance_repository.get_user_maintenance_item(item_id)
        if not item or item.user_id != self.user.id:
            return None

        # Если не передан пробег, получаем текущий пробег автомобиля
        if service_odometer is None:
            vehicle = await self.vehicle_repository.get_vehicle(item.vehicle_id)
            if vehicle:
                service_odometer = vehicle.odometer

        # Используем переданный комментарий или создаем стандартный
        if comment is None or comment.strip() == "":
            comment = f"Обслуживание выполнено {service_date.strftime('%d.%m.%Y')}"

        # Создаем запись об обслуживании
        record_data = {
            "user_item_id": item_id,
            "service_date": service_date,
            "service_odometer": service_odometer,
            "comment": comment,
        }

        # if photo_path:
        #     record_data["photo_path"] = photo_path

        return await self.maintenance_repository.create_service_record(record_data)

    async def get_items_requiring_service(
        self, vehicle_id: uuid.UUID, page: int = 1, page_size: int = 10
    ) -> Tuple[List[MaintenanceItemDisplay], Dict[str, int]]:
        """
        Получить элементы, требующие обслуживания для конкретного автомобиля.
        Возвращает список элементов в формате отображения и информацию о пагинации.
        """
        # Вычисляем параметры пагинации
        skip = (page - 1) * page_size
        limit = page_size

        # Получаем элементы, требующие обслуживания
        items, total_count = (
            await self.maintenance_repository.get_maintenance_items_requiring_service(
                self.user.id, vehicle_id, skip, limit
            )
        )

        # Получаем информацию о текущем пробеге автомобиля
        vehicle = await self.vehicle_repository.get_vehicle(vehicle_id)
        if not vehicle:
            return [], {
                "current_page": page,
                "total_pages": 0,
                "items_per_page": page_size,
                "total_items": 0,
            }

        current_odometer = vehicle.odometer

        # Преобразуем в формат отображения с дополнительной информацией
        display_items = []
        for item in items:
            # Определяем интервал обслуживания
            interval = item.custom_interval or item.maintenance_item.default_interval

            # Определяем статус
            status = MaintenanceItemStatus.OK

            if item.last_service_odometer is None:
                status = MaintenanceItemStatus.NEVER_SERVICED
                overdue_km = None
                remaining_km = None
            else:
                km_since_last_service = current_odometer - item.last_service_odometer

                if km_since_last_service > interval:
                    status = MaintenanceItemStatus.OVERDUE
                    overdue_km = km_since_last_service - interval
                    remaining_km = None
                elif km_since_last_service > interval * 0.9:
                    status = MaintenanceItemStatus.UPCOMING
                    overdue_km = None
                    remaining_km = interval - km_since_last_service
                else:
                    # Элемент не требует обслуживания в ближайшее время
                    continue

            # Определяем тип детали на основе названия, если не задан явно
            item_type = MaintenanceItemType.OTHER
            item_name = item.maintenance_item.name.lower()

            if "масл" in item_name:
                item_type = MaintenanceItemType.OIL_CHANGE
            elif "тормоз" in item_name or "колод" in item_name:
                item_type = MaintenanceItemType.BRAKE_PADS
            elif "ремен" in item_name or "грм" in item_name:
                item_type = MaintenanceItemType.TIMING_BELT
            elif "фильтр" in item_name and (
                "воздух" in item_name or "воздуш" in item_name
            ):
                item_type = MaintenanceItemType.AIR_FILTER
            elif "аккумулятор" in item_name or "батар" in item_name:
                item_type = MaintenanceItemType.BATTERY

            # Создаем объект отображения
            # Преобразуем datetime в date для last_service_date, если он не None
            last_service_date = None
            if item.last_service_date:
                if isinstance(item.last_service_date, datetime):
                    last_service_date = item.last_service_date.date()
                else:
                    last_service_date = item.last_service_date

            display_item = MaintenanceItemDisplay(
                id=item.id,
                name=item.maintenance_item.name,
                type=item_type,
                status=status,
                last_service_date=last_service_date,
                last_service_odometer=item.last_service_odometer,
                overdue_km=overdue_km,
                remaining_km=remaining_km,
                custom_interval=item.custom_interval,
                default_interval=item.maintenance_item.default_interval,
            )

            display_items.append(display_item)

        # Информация о пагинации
        total_pages = (total_count + page_size - 1) // page_size  # Округление вверх
        pagination = {
            "current_page": page,
            "total_pages": total_pages,
            "items_per_page": page_size,
            "total_items": total_count,
        }

        return display_items, pagination
