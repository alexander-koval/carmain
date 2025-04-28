import uuid
from typing import List
import datetime

from fastapi import APIRouter, Depends, Form, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.requests import Request

from carmain.services.vehicle_service import VehicleService
from carmain.schema.vehicle_schema import (
    VehicleSchema,
    VehicleCreate,
    VehicleUpdate,
)
from carmain.models.users import User
from carmain.routers.v1.auth_router import current_active_verified_user

vehicle_router = APIRouter(prefix="/vehicles", tags=["vehicles"])
templates = Jinja2Templates(directory="carmain/templates")


@vehicle_router.get("/", response_class=HTMLResponse)
async def list_vehicles(
    request: Request, vehicle_service: VehicleService = Depends()
):
    """Возвращает HTML-фрагмент со списком автомобилей пользователя"""
    vehicles = await vehicle_service.get_user_vehicles()
    return templates.TemplateResponse(
        request=request, name="vehicle_list.html", context={"vehicles": vehicles}
    )


@vehicle_router.get(path="/{obj_id}", response_class=HTMLResponse)
async def get(
    request: Request, obj_id: uuid.UUID, vehicle_service: VehicleService = Depends()
):
    vehicle = await vehicle_service.get_by_id(obj_id)
    schema = VehicleSchema.model_validate(vehicle)
    return templates.TemplateResponse(
        request=request, name="vehicle.html", context={"vehicle": schema}
    )


@vehicle_router.post(path="/create", response_class=HTMLResponse)
async def create(
    request: Request,
    brand: str = Form(...),
    model: str = Form(...),
    year: str = Form(...),
    odometer: int = Form(...),
    vehicle_service: VehicleService = Depends(),
    user: User = Depends(current_active_verified_user),
):
    try:
        year_date = datetime.date.fromisoformat(year)
        vehicle_data = VehicleCreate(
            brand=brand,
            model=model,
            year=year_date,
            odometer=odometer,
            user_id=user.id
        )
        
        await vehicle_service.add(vehicle_data)
        
        # Возвращаем редирект для полного обновления страницы
        return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
    except Exception as e:
        return templates.TemplateResponse(
            request=request,
            name="error_partial.html",
            context={"error": f"Ошибка при создании автомобиля: {str(e)}"},
            status_code=status.HTTP_400_BAD_REQUEST
        )


@vehicle_router.patch(path="/{obj_id}/update", response_class=HTMLResponse)
async def update(
    request: Request,
    obj_id: uuid.UUID,
    year: str = Form(...),
    odometer: int = Form(...),
    brand: str = Form(...),
    model: str = Form(...),
    vehicle_service: VehicleService = Depends(),
    user: User = Depends(current_active_verified_user),
):
    try:
        year_date = datetime.date.fromisoformat(year)
        vehicle_data = VehicleUpdate(
            brand=brand,
            model=model,
            year=year_date,
            odometer=odometer
        )
        
        # Обновляем данные автомобиля
        updated_vehicle = await vehicle_service.patch(obj_id, vehicle_data)
        
        # Возвращаем только обновленную карточку автомобиля
        return templates.TemplateResponse(
            request=request,
            name="vehicle_card.html",
            context={"vehicle": updated_vehicle}
        )
    except Exception as e:
        return templates.TemplateResponse(
            request=request,
            name="error_partial.html",
            context={"error": f"Ошибка при обновлении автомобиля: {str(e)}"},
            status_code=status.HTTP_400_BAD_REQUEST
        )
