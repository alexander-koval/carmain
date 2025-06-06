import uuid
from typing import Annotated, Any
from collections.abc import Sequence
from fastapi import Depends

from carmain.models.users import User
from carmain.models.vehicles import Vehicle
from carmain.repository.vehicle_repository import VehicleRepository
from carmain.routers.v1.auth_router import current_active_verified_user
from carmain.schemas.vehicle_schema import VehicleSchema
from carmain.services.base_service import BaseService


class VehicleService(BaseService[uuid.UUID, VehicleSchema, Vehicle]):
    def __init__(
        self,
        repository: Annotated[VehicleRepository, Depends(VehicleRepository)],
        user: User = Depends(current_active_verified_user),
    ):
        self.repository = repository
        self.user = user

    async def get_by_id(self, obj_id: uuid.UUID) -> Vehicle:
        return await self.repository.get_by_id(obj_id)

    async def add(self, schema: VehicleSchema) -> Vehicle:
        vehicle = Vehicle(**schema.model_dump())
        vehicle.user_id = self.user.id
        return await self.repository.create(vehicle)

    async def patch(self, obj_id: uuid.UUID, schema: VehicleSchema) -> Vehicle:
        update_data: dict[str, Any] = schema.model_dump(
            exclude_unset=True, exclude_defaults=True, exclude_none=True
        )
        return await self.repository.update_by_id(obj_id, update_data)

    async def remove_by_id(self, obj_id: uuid.UUID) -> Vehicle:
        return await self.repository.delete_by_id(obj_id)

    async def all(self) -> Sequence[Vehicle]:
        return await self.repository.all()

    async def get_user_vehicles(self) -> list[Vehicle]:
        """Get all vehicles belonging to the current user"""
        return await self.repository.get_by_user_id(self.user.id)
