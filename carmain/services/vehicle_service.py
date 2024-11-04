import uuid
from typing import Annotated, Optional

from fastapi import Depends

from carmain.models.users import User
from carmain.models.vehicles import Vehicle
from carmain.repository.vehicle_repository import VehicleRepository
from carmain.routers import auth_router
from carmain.routers.auth_router import current_active_verified_user
from carmain.schema.vehicle_schema import VehicleSchema
from carmain.services.base_service import BaseService, M, K


class VehicleService(BaseService[uuid.UUID, VehicleSchema]):
    def __init__(
        self,
        repository: Annotated[VehicleRepository, Depends(VehicleRepository)],
        user: User = Depends(current_active_verified_user),
    ):
        self.repository = repository
        self.user = user

    async def get_by_id(self, obj_id: uuid.UUID) -> VehicleSchema:
        return await super().get_by_id(obj_id)

    async def add(self, schema: VehicleSchema) -> VehicleSchema:
        return None

    async def patch(self, obj_id: uuid.UUID, schema: VehicleSchema) -> VehicleSchema:
        return VehicleSchema()

    async def remove_by_id(self, obj_id: uuid.UUID) -> VehicleSchema:
        return VehicleSchema()

    async def all(self) -> list[VehicleSchema]:
        return await self.repository.all()
