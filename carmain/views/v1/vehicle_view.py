import uuid
from typing import List
import datetime

from fastapi import APIRouter, Depends, Form, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.requests import Request

from carmain.services.vehicle_service import VehicleService
from carmain.services.maintenance_service import MaintenanceService
from carmain.schema.vehicle_schema import (
    VehicleSchema,
    VehicleCreate,
    VehicleUpdate,
)
from carmain.models.users import User
from carmain.routers.v1.auth_router import current_active_verified_user

vehicle_router = APIRouter(prefix="/vehicles", tags=["vehicles"])
templates = Jinja2Templates(directory="carmain/templates")


@vehicle_router.get("/")
async def list_vehicles(
    request: Request,
    vehicle_service: VehicleService = Depends(),
    maintenance_service: MaintenanceService = Depends(),
):
    """Возвращает HTML-фрагмент со списком автомобилей пользователя"""
    vehicles = await vehicle_service.get_user_vehicles()
    service_requiring = {
        vehicle.id.hex: await maintenance_service.get_items_requiring_service_count(
            vehicle.id
        )
        for vehicle in vehicles
    }
    return templates.TemplateResponse(
        request=request,
        name="vehicle_list.html",
        context={"vehicles": vehicles, "service_requiring": service_requiring},
    )


@vehicle_router.get(path="/{obj_id}")
async def get(
    request: Request, obj_id: uuid.UUID, vehicle_service: VehicleService = Depends()
):
    vehicle = await vehicle_service.get_by_id(obj_id)
    schema = VehicleSchema.model_validate(vehicle)
    return templates.TemplateResponse(
        request=request, name="vehicle.html", context={"vehicle": schema}
    )


@vehicle_router.post(path="/create")
async def create(
    request: Request,
    brand: str = Form(...),
    model: str = Form(...),
    year: int = Form(...),
    odometer: int = Form(...),
    vehicle_service: VehicleService = Depends(),
    user: User = Depends(current_active_verified_user),
):
    try:
        vehicle_data = VehicleCreate(
            brand=brand, model=model, year=year, odometer=odometer, user_id=user.id
        )

        await vehicle_service.add(vehicle_data)

        return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
    except Exception as e:
        return templates.TemplateResponse(
            request=request,
            name="error_partial.html",
            context={"error": f"Ошибка при создании автомобиля: {str(e)}"},
            status_code=status.HTTP_400_BAD_REQUEST,
        )


@vehicle_router.patch(path="/{obj_id}/update")
async def update(
    request: Request,
    obj_id: uuid.UUID,
    year: int = Form(...),
    odometer: int = Form(...),
    brand: str = Form(...),
    model: str = Form(...),
    vehicle_service: VehicleService = Depends(),
    maintenance_service: MaintenanceService = Depends(),
    user: User = Depends(current_active_verified_user),
):
    try:
        vehicle_data = VehicleUpdate(
            brand=brand, model=model, year=year, odometer=odometer
        )

        updated_vehicle = await vehicle_service.patch(obj_id, vehicle_data)

        service_requiring = {
            updated_vehicle.id.hex: await maintenance_service.get_items_requiring_service_count(
                updated_vehicle.id
            )
        }

        return templates.TemplateResponse(
            request=request,
            name="vehicle_card.html",
            context={
                "vehicle": updated_vehicle,
                "service_requiring": service_requiring,
            },
        )
    except Exception as e:
        return templates.TemplateResponse(
            request=request,
            name="error_partial.html",
            context={"error": f"Ошибка при обновлении автомобиля: {str(e)}"},
            status_code=status.HTTP_400_BAD_REQUEST,
        )
