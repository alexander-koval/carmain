import uuid
from datetime import date
from typing import List, Optional, Tuple, Annotated
from collections.abc import Sequence

from dns.resolver import query
from fastapi import Depends
from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from carmain.core.database import get_async_session
from carmain.core.exceptions import NotFoundError
from carmain.models.items import MaintenanceItem, UserMaintenanceItem
from carmain.models.records import ServiceRecord
from carmain.models.vehicles import Vehicle
from carmain.repository.base_repository import BaseRepository


class UserMaintenanceRepository(BaseRepository):
    def __init__(self, session: Annotated[AsyncSession, Depends(get_async_session)]):
        super().__init__(UserMaintenanceItem, session)

    async def get_by_vehicle(
        self, vehicle_id: uuid.UUID, skip=0, limit=10, eager=False
    ) -> Sequence[UserMaintenanceItem]:
        query = select(self.model).where(UserMaintenanceItem.vehicle_id == vehicle_id)
        if eager:
            for eager in getattr(self.model, "eagers", []):
                query = query.options(joinedload(getattr(self.model, eager)))
        query = query.offset(skip).limit(limit)
        result = await self.session.scalars(query)
        if not result:
            raise NotFoundError(detail=f"not found for vehicle_id : {vehicle_id}")
        return result.unique().all()

    async def get_by_item_id(
        self, item_id: uuid.UUID, skip=0, limit=10, eager=False
    ) -> UserMaintenanceItem:
        query = select(self.model).where(UserMaintenanceItem.item_id == item_id)
        if eager:
            for eager in getattr(self.model, "eagers", []):
                query = query.options(joinedload(getattr(self.model, eager)))
        query = query.offset(skip).limit(limit)
        result = await self.session.scalar(query)
        if not result:
            raise NotFoundError(detail=f"not found for vehicle_id : {item_id}")
        return result


class MaintenanceRepository(BaseRepository):
    """Репозиторий для работы с данными обслуживания автомобилей"""

    def __init__(
        self, session: Annotated[AsyncSession, Depends(get_async_session)]
    ) -> None:
        super().__init__(MaintenanceItem, session)

    async def get_maintenance_items(
        self, skip: int = 0, limit: int = 10
    ) -> Sequence[MaintenanceItem]:
        """Получить список всех типов обслуживания"""
        query = select(MaintenanceItem).offset(skip).limit(limit)
        result = await self.session.execute(query)
        return result.scalars().unique().all()

    async def get_maintenance_item(
        self, item_id: uuid.UUID
    ) -> Optional[MaintenanceItem]:
        """Получить информацию о типе обслуживания по ID"""
        query = select(MaintenanceItem).where(MaintenanceItem.id == item_id)
        result = await self.session.execute(query)
        return result.unique().scalar_one_or_none()

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
        return result.unique().scalar_one_or_none()

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

    async def get_service_records(
        self, user_item_id: uuid.UUID
    ) -> Sequence[ServiceRecord]:
        """Получить историю обслуживания для конкретного элемента"""
        query = (
            select(ServiceRecord)
            .where(ServiceRecord.user_item_id == user_item_id)
            .order_by(ServiceRecord.service_date.desc())
        )
        result = await self.session.execute(query)
        return result.scalars().unique().all()

    async def get_maintenance_items_requiring_service(
        self, user_id: int, vehicle_id: uuid.UUID, skip: int = 0, limit: int = 10
    ) -> Sequence[UserMaintenanceItem]:
        """
        Получить элементы, требующие обслуживания для конкретного автомобиля.
        Возвращает кортеж (список элементов, общее количество)
        """

        vehicle_query = select(Vehicle).where(
            and_(Vehicle.id == vehicle_id, Vehicle.user_id == user_id)
        )
        vehicle_result = await self.session.execute(vehicle_query)
        vehicle = vehicle_result.scalar_one_or_none()

        if not vehicle:
            return []

        current_odometer = vehicle.odometer

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

        return items
