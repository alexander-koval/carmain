import uuid
from typing import List

from fastapi import APIRouter, Depends

from carmain.schema.vehicle_schema import (
    VehicleSchema,
    VehicleCreate,
    VehicleUpdate,
)
from carmain.services.vehicle_service import VehicleService

vehicle_router = APIRouter(prefix="/vehicles", tags=["vehicles"])


@vehicle_router.get(path="/", response_model=List[VehicleSchema])
async def index(
    vehicle_service: VehicleService = Depends(),
):
    return await vehicle_service.all()


@vehicle_router.get(path="/{id}", response_model=VehicleSchema)
async def get(obj_id: uuid.UUID, vehicle_service: VehicleService = Depends()):
    return await vehicle_service.get_by_id(obj_id)


@vehicle_router.post(path="/create", response_model=VehicleSchema)
async def create(
    vehicle: VehicleCreate,
    vehicle_service: VehicleService = Depends(),
):
    return await vehicle_service.add(vehicle)


@vehicle_router.patch(path="/update", response_model=VehicleSchema)
async def update(
    obj_id: uuid.UUID,
    vehicle: VehicleUpdate,
    vehicle_service: VehicleService = Depends(),
):
    return await vehicle_service.patch(obj_id, vehicle)


@vehicle_router.delete(path="/{id}", response_model=VehicleSchema)
async def delete(obj_id: uuid.UUID, vehicle_service: VehicleService = Depends()):
    return await vehicle_service.remove_by_id(obj_id)
