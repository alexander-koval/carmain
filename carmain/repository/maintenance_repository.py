import uuid
from datetime import date
from typing import List, Optional, Tuple, Annotated

from fastapi import Depends
from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from carmain.core.database import get_async_session
from carmain.models.items import MaintenanceItem, UserMaintenanceItem
from carmain.models.records import ServiceRecord
from carmain.models.vehicles import Vehicle
from carmain.repository.base_repository import BaseRepository


class MaintenanceRepository(BaseRepository):
    """Репозиторий для работы с данными обслуживания автомобилей"""

    def __init__(
        self, session: Annotated[AsyncSession, Depends(get_async_session)]
    ) -> None:
        super().__init__(MaintenanceItem, session)

    async def get_maintenance_items(
        self, skip: int = 0, limit: int = 10
    ) -> List[MaintenanceItem]:
        """Получить список всех типов обслуживания"""
        query = select(MaintenanceItem).offset(skip).limit(limit)
        result = await self.session.execute(query)
        return result.scalars().unique().all()

    async def get_maintenance_item(self, item_id: int) -> Optional[MaintenanceItem]:
        """Получить информацию о типе обслуживания по ID"""
        query = select(MaintenanceItem).where(MaintenanceItem.id == item_id)
        result = await self.session.execute(query)
        return result.unique().scalar_one_or_none()

    async def create_maintenance_item(self, item: dict) -> MaintenanceItem:
        """Создать новый тип обслуживания"""
        db_item = MaintenanceItem(**item)
        self.session.add(db_item)
        await self.session.commit()
        await self.session.refresh(db_item)
        return db_item

    async def get_user_maintenance_items(
        self,
        user_id: int,
        vehicle_id: Optional[uuid.UUID] = None,
        skip: int = 0,
        limit: int = 10,
    ) -> List[UserMaintenanceItem]:
        """Получить список элементов обслуживания пользователя"""
        query = select(UserMaintenanceItem).where(
            UserMaintenanceItem.user_id == user_id
        )

        if vehicle_id:
            query = query.where(UserMaintenanceItem.vehicle_id == vehicle_id)

        query = (
            query.options(joinedload(UserMaintenanceItem.maintenance_item))
            .offset(skip)
            .limit(limit)
        )
        result = await self.session.execute(query)
        return result.scalars().unique().all()

    async def get_vehicle_maintenance_items_count(
        self, user_id: int, vehicle_id: uuid.UUID
    ) -> int:
        """Получить количество элементов обслуживания для конкретного автомобиля"""
        query = select(func.count()).where(
            and_(
                UserMaintenanceItem.user_id == user_id,
                UserMaintenanceItem.vehicle_id == vehicle_id,
            )
        )
        result = await self.session.execute(query)
        return result.scalar_one()

    async def get_user_maintenance_item(
        self, item_id: uuid.UUID
    ) -> Optional[UserMaintenanceItem]:
        """Получить элемент обслуживания пользователя по ID"""
        query = (
            select(UserMaintenanceItem)
            .where(UserMaintenanceItem.id == item_id)
            .options(joinedload(UserMaintenanceItem.maintenance_item))
        )
        result = await self.session.execute(query)
        # scalar_one_or_none не требует unique() так как возвращает один объект
        return result.scalar_one_or_none()

    async def create_user_maintenance_item(
        self, user_id: int, item_data: dict
    ) -> UserMaintenanceItem:
        """Создать элемент обслуживания для пользователя"""
        db_item = UserMaintenanceItem(user_id=user_id, **item_data)
        self.session.add(db_item)
        await self.session.commit()
        await self.session.refresh(db_item)
        return db_item

    async def update_user_maintenance_item(
        self, item_id: uuid.UUID, update_data: dict
    ) -> Optional[UserMaintenanceItem]:
        """Обновить элемент обслуживания пользователя"""
        query = select(UserMaintenanceItem).where(UserMaintenanceItem.id == item_id)
        result = await self.session.execute(query)
        db_item = result.scalar_one_or_none()

        if db_item:
            for key, value in update_data.items():
                if hasattr(db_item, key) and value is not None:
                    setattr(db_item, key, value)

            await self.session.commit()
            await self.session.refresh(db_item)

        return db_item

    async def delete_user_maintenance_item(self, item_id: uuid.UUID) -> bool:
        """Удалить элемент обслуживания пользователя"""
        query = select(UserMaintenanceItem).where(UserMaintenanceItem.id == item_id)
        result = await self.session.execute(query)
        db_item = result.scalar_one_or_none()

        if db_item:
            await self.session.delete(db_item)
            await self.session.commit()
            return True

        return False

    async def get_service_records(self, user_item_id: uuid.UUID) -> List[ServiceRecord]:
        """Получить историю обслуживания для конкретного элемента"""
        query = (
            select(ServiceRecord)
            .where(ServiceRecord.user_item_id == user_item_id)
            .order_by(ServiceRecord.service_date.desc())
        )
        result = await self.session.execute(query)
        return result.scalars().unique().all()

    async def create_service_record(self, record_data: dict) -> ServiceRecord:
        """Создать запись об обслуживании"""
        db_record = ServiceRecord(**record_data)
        self.session.add(db_record)
        await self.session.commit()
        await self.session.refresh(db_record)

        # Обновляем информацию о последнем обслуживании в UserMaintenanceItem
        user_item_id = record_data.get("user_item_id")
        service_date = record_data.get("service_date")
        service_odometer = record_data.get("service_odometer")

        if user_item_id and (service_date or service_odometer):
            query = select(UserMaintenanceItem).where(
                UserMaintenanceItem.id == user_item_id
            )
            result = await self.session.execute(query)
            user_item = result.scalar_one_or_none()

            if user_item:
                if service_date:
                    user_item.last_service_date = service_date
                if service_odometer:
                    user_item.last_service_odometer = service_odometer
                await self.session.commit()

        return db_record

    async def get_maintenance_items_requiring_service(
        self, user_id: int, vehicle_id: uuid.UUID, skip: int = 0, limit: int = 10
    ) -> Tuple[List[UserMaintenanceItem], int]:
        """
        Получить элементы, требующие обслуживания для конкретного автомобиля.
        Возвращает кортеж (список элементов, общее количество)
        """
        # Сначала получаем информацию о текущем пробеге автомобиля
        vehicle_query = select(Vehicle).where(
            and_(Vehicle.id == vehicle_id, Vehicle.user_id == user_id)
        )
        vehicle_result = await self.session.execute(vehicle_query)
        vehicle = vehicle_result.scalar_one_or_none()

        if not vehicle:
            return [], 0

        current_odometer = vehicle.odometer

        # Запрос для получения элементов, требующих обслуживания
        query = (
            select(UserMaintenanceItem)
            .where(
                and_(
                    UserMaintenanceItem.user_id == user_id,
                    UserMaintenanceItem.vehicle_id == vehicle_id,
                    or_(
                        # Никогда не обслуживалось
                        UserMaintenanceItem.last_service_odometer.is_(None),
                        # Просрочено по пробегу
                        and_(
                            UserMaintenanceItem.last_service_odometer.isnot(None),
                            current_odometer - UserMaintenanceItem.last_service_odometer
                            > func.coalesce(
                                UserMaintenanceItem.custom_interval,
                                select(MaintenanceItem.default_interval)
                                .where(
                                    MaintenanceItem.id == UserMaintenanceItem.item_id
                                )
                                .scalar_subquery(),
                            ),
                        ),
                        # Скоро требуется обслуживание (осталось менее 10% от интервала)
                        and_(
                            UserMaintenanceItem.last_service_odometer.isnot(None),
                            current_odometer - UserMaintenanceItem.last_service_odometer
                            > func.coalesce(
                                UserMaintenanceItem.custom_interval,
                                select(MaintenanceItem.default_interval)
                                .where(
                                    MaintenanceItem.id == UserMaintenanceItem.item_id
                                )
                                .scalar_subquery(),
                            )
                            * 0.9,
                        ),
                    ),
                )
            )
            .options(joinedload(UserMaintenanceItem.maintenance_item))
        )

        # Получаем общее количество элементов для пагинации
        count_query = select(func.count()).select_from(query.subquery())
        count_result = await self.session.execute(count_query)
        total_count = count_result.scalar_one()

        # Добавляем пагинацию и сортировку
        # Сначала просроченные, затем подходящие к сроку
        query = (
            query.order_by(
                # Сначала никогда не обслуживаемые
                UserMaintenanceItem.last_service_odometer.is_(None).desc(),
                # Затем по уровню просрочки (насколько превышен интервал)
                (
                    current_odometer
                    - UserMaintenanceItem.last_service_odometer
                    - func.coalesce(
                        UserMaintenanceItem.custom_interval,
                        select(MaintenanceItem.default_interval)
                        .where(MaintenanceItem.id == UserMaintenanceItem.item_id)
                        .scalar_subquery(),
                    )
                ).desc(),
            )
            .offset(skip)
            .limit(limit)
        )

        result = await self.session.execute(query)
        # Используем unique() для предотвращения дублирования записей при joinedload с коллекциями
        items = result.scalars().unique().all()

        return items, total_count
