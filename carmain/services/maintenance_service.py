import sys
import uuid
from datetime import date, datetime
from typing import List, Optional, Dict, Any, Tuple, Annotated, Sequence, Coroutine

from fastapi import Depends, HTTPException
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
    ServiceRecordCreate,
    UserMaintenanceItemUpdate,
    ServiceRecordUpdate,
)
from carmain.services.base_service import BaseService
from carmain.routers.v1.auth_router import current_active_verified_user
from carmain.utils.maintenance_utils import get_maintenance_item_type


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

    async def get_user_maintenance_item_by_item_id(self, item_id: uuid.UUID):
        """Получить элемент обслуживания пользователя по Maintenance ID"""
        return await self.user_maintenance_repository.get_by_item_id(
            item_id, eager=True
        )

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

    async def create_service_record(self, record: ServiceRecordCreate) -> ServiceRecord:
        """Создать запись об обслуживании"""
        record_data = record.model_dump(exclude_unset=True)
        db_item = ServiceRecord(**record_data)
        return await self.record_repository.create(db_item)

    async def mark_item_as_serviced(
        self,
        service_record_create: ServiceRecordCreate,
    ) -> Optional[UserMaintenanceItem]:
        """Отметить элемент как обслуженный"""

        item: UserMaintenanceItem = await self.user_maintenance_repository.get_by_id(
            service_record_create.user_item_id, eager=True
        )
        if not item or item.user_id != self.user.id:
            raise HTTPException(
                status_code=404, detail="Элемент обслуживания не найден"
            )

        if service_record_create.service_odometer is None:
            if item.vehicle:
                service_record_create.service_odometer = item.vehicle.odometer

        if (
            service_record_create.comment is None
            or service_record_create.comment.strip() == ""
        ):
            service_record_create.comment = f"Обслуживание выполнено {service_record_create.service_date.strftime('%d.%m.%Y')}"

        record_data = service_record_create.model_dump(
            exclude_unset=True, exclude_defaults=True, exclude_none=True
        )

        # if photo_path:
        #     record_data["photo_path"] = photo_path
        db_record = ServiceRecord(**record_data)
        await self.record_repository.create(db_record)

        user_maintenance_item_update = UserMaintenanceItemUpdate(
            user_item_id=item.id,
            last_service_odometer=service_record_create.service_odometer,
            last_service_date=service_record_create.service_date,
        )
        maintenance_item_payload = user_maintenance_item_update.model_dump(
            exclude_unset=True, exclude_defaults=True, exclude_none=True
        )
        db_item: UserMaintenanceItem = (
            await self.user_maintenance_repository.update_by_id(
                item.id, maintenance_item_payload
            )
        )

        updated_item = await self.user_maintenance_repository.get_by_id(
            item.id, eager=True
        )
        return updated_item

    async def get_items_requiring_service_count(self, vehicle_id: uuid.UUID) -> int:
        items = (
            await self.maintenance_repository.get_maintenance_items_requiring_service(
                self.user.id, vehicle_id, 0, sys.maxsize
            )
        )
        return len(items)

    async def get_items_requiring_service(
        self,
        vehicle_id: uuid.UUID,
        page: int = 1,
        page_size: int = 10,
        show_all: bool = False,
    ) -> Tuple[List[MaintenanceItemDisplay], Dict[str, int]]:
        """
        Получить элементы, требующие обслуживания для конкретного автомобиля.
        Возвращает список элементов в формате отображения и информацию о пагинации.

        Args:
            vehicle_id: ID автомобиля
            page: Номер страницы (по умолчанию 1)
            page_size: Размер страницы (по умолчанию 10)
            show_all: Показать все элементы, включая не требующие обслуживания (по умолчанию False)
        """

        vehicle = await self.vehicle_repository.get_vehicle(vehicle_id)
        if not vehicle:
            return [], {
                "current_page": page,
                "total_pages": 0,
                "items_per_page": page_size,
                "total_items": 0,
            }

        current_odometer = vehicle.odometer

        if not show_all:
            all_items = await self.maintenance_repository.get_maintenance_items_requiring_service(
                self.user.id, vehicle_id, 0, sys.maxsize
            )
        else:
            all_items = await self.maintenance_repository.get_user_maintenance_items(
                self.user.id, vehicle_id, 0, sys.maxsize
            )

        filtered_items = []
        for item in all_items:
            interval = item.custom_interval or item.maintenance_item.default_interval
            status = MaintenanceItemStatus.OK

            if item.last_service_odometer is None:
                status = MaintenanceItemStatus.NEVER_SERVICED
            else:
                km_since_last_service = current_odometer - item.last_service_odometer
                if km_since_last_service > interval:
                    status = MaintenanceItemStatus.OVERDUE
                elif km_since_last_service > interval * 0.9:
                    status = MaintenanceItemStatus.UPCOMING
                else:
                    if not show_all:
                        continue
            filtered_items.append(item)

        total_count = len(filtered_items)

        skip = (page - 1) * page_size
        limit = page_size
        paginated_items = filtered_items[skip : skip + limit]

        display_items = []
        for item in paginated_items:

            interval = item.custom_interval or item.maintenance_item.default_interval

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
                    if not show_all:
                        continue
                    overdue_km = None
                    remaining_km = interval - km_since_last_service

            item_type = get_maintenance_item_type(item.maintenance_item.name)

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

        total_pages = (total_count + page_size - 1) // page_size
        pagination = {
            "current_page": page,
            "total_pages": total_pages,
            "items_per_page": page_size,
            "total_items": total_count,
        }

        return display_items, pagination

    async def update_service_record(
        self,
        record_id: int,
        service_record_update: ServiceRecordUpdate,
    ) -> ServiceRecord:
        """Обновить запись об обслуживании"""
        record = await self.record_repository.get_by_id(record_id)
        user_item = await self.user_maintenance_repository.get_by_id(
            record.user_item_id
        )
        if user_item.user_id != self.user.id:
            raise HTTPException(
                status_code=404, detail="Запись обслуживания не найдена"
            )
        update_data = service_record_update.model_dump(
            exclude_unset=True, exclude_defaults=True, exclude_none=True
        )
        update_data.pop("user_item_id", None)
        updated = await self.record_repository.update_by_id(record_id, update_data)
        return updated
