from typing import List, Optional, Annotated

from fastapi import APIRouter, Depends

from carmain.models.users import User
from carmain.routers import auth_router
from carmain.schema.vehicle_schema import VehicleSchema, VehicleFind, VehicleCreate
from carmain.services.vehicle_service import VehicleService

vehicle_router = APIRouter(prefix="/vehicles", tags=["vehicles"])


@vehicle_router.get(path="/", response_model=List[VehicleSchema])
async def index(
    vehicle_service: VehicleService = Depends(),
):
    return await vehicle_service.all()


@vehicle_router.post(path="/create", response_model=VehicleSchema)
async def create_vehicle(
    vehicle: VehicleCreate,
    vehicle_service: VehicleService = Depends(),
):
    return await vehicle_service.add(vehicle)
