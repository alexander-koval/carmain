import uuid
from typing import List

from fastapi import APIRouter, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.requests import Request

from carmain.services.vehicle_service import VehicleService
from carmain.schema.vehicle_schema import (
    VehicleSchema,
    VehicleCreate,
    VehicleUpdate,
)

vehicle_router = APIRouter(prefix="/vehicles", tags=["vehicles"])
templates = Jinja2Templates(directory="carmain/templates")


@vehicle_router.get(path="/{obj_id}", response_class=HTMLResponse)
async def get(
    request: Request, obj_id: uuid.UUID, vehicle_service: VehicleService = Depends()
):
    vehicle = await vehicle_service.get_by_id(obj_id)
    schema = VehicleSchema.model_validate(vehicle)
    return templates.TemplateResponse(
        request=request, name="vehicle.html", context={"id": obj_id}
    )
