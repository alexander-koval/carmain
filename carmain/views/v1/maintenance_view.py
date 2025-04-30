from datetime import date
import uuid
from typing import Optional, List, Dict, Any, Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, Query, Path
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession

from carmain.core.database import get_async_session
from carmain.routers.v1.auth_router import current_active_verified_user
from carmain.models.users import User
from carmain.repository.maintenance_repository import MaintenanceRepository
from carmain.repository.vehicle_repository import VehicleRepository
from carmain.schemas.maintenance_schema import (
    MaintenanceItemDisplay,
    ServiceRecordCreate,
    PaginationParams,
)
from carmain.services.maintenance_service import MaintenanceService


router = APIRouter(prefix="/vehicles", tags=["maintenance"])

# Настройка шаблонизатора
templates = Jinja2Templates(directory="carmain/templates")


# Используем инъекцию зависимостей напрямую через MaintenanceService


@router.get("/{vehicle_id}/maintenance", response_class=HTMLResponse)
async def get_maintenance_items_view(
    request: Request,
    vehicle_id: Annotated[uuid.UUID, Path(description="UUID идентификатор автомобиля")],
    maintenance_service: Annotated[MaintenanceService, Depends()],
    page: int = Query(1, ge=1),
):
    """
    Отображение деталей, требующих обслуживания для конкретного автомобиля
    """
    # Получаем автомобиль и проверяем, что он принадлежит пользователю
    vehicle = await maintenance_service.get_vehicle(vehicle_id)
    if not vehicle or vehicle.user_id != maintenance_service.user.id:
        raise HTTPException(status_code=404, detail="Автомобиль не найден")

    # Получаем все автомобили пользователя (для выпадающего списка)
    user_vehicles = await maintenance_service.get_user_vehicles()

    # Получаем элементы, требующие обслуживания
    maintenance_items, pagination = (
        await maintenance_service.get_items_requiring_service(
            vehicle_id=vehicle_id,
            page=page,
            page_size=10,  # Константа или из конфигурации
        )
    )

    # Преобразуем пагинацию в DTO для передачи в шаблон
    pagination_params = PaginationParams(
        current_page=pagination["current_page"],
        total_pages=pagination["total_pages"],
        items_per_page=pagination["items_per_page"],
        total_items=pagination["total_items"],
    )

    # Проверяем, является ли запрос HTMX запросом с hx-target
    is_htmx_request = request.headers.get("HX-Request") == "true"
    
    # Если это HTMX запрос, возвращаем только список элементов
    if is_htmx_request:
        return templates.TemplateResponse(
            "maintenance_items_list.html",
            {
                "request": request,
                "vehicle": vehicle,
                "maintenance_items": maintenance_items,
                "pagination": pagination_params,
            },
        )
    
    # Иначе возвращаем полную страницу
    return templates.TemplateResponse(
        "maintenance_items.html",
        {
            "request": request,
            "user": maintenance_service.user,
            "vehicle": vehicle,
            "user_vehicles": user_vehicles,
            "maintenance_items": maintenance_items,
            "pagination": pagination_params,
        },
    )


@router.get("/{vehicle_id}/all-maintenance-items", response_class=HTMLResponse)
async def get_all_maintenance_items_view(
    request: Request,
    vehicle_id: Annotated[uuid.UUID, Path(description="UUID идентификатор автомобиля")],
    maintenance_service: Annotated[MaintenanceService, Depends()],
    page: int = Query(1, ge=1),
):
    """
    Отображение всех отслеживаемых деталей для автомобиля
    """
    # Реализация для вывода всех деталей
    # ...
    # Временная заглушка
    return templates.TemplateResponse(
        "maintenance_items_all.html",
        {
            "request": request,
            "user": maintenance_service.user,
            "vehicle_id": vehicle_id,
            "message": "Эта страница еще в разработке. Скоро здесь будут отображаться все детали.",
        },
    )


@router.post(
    "/{vehicle_id}/maintenance-items/{item_id}/service", response_class=HTMLResponse
)
async def mark_item_as_serviced(
    request: Request,
    vehicle_id: Annotated[uuid.UUID, Path(description="UUID идентификатор автомобиля")],
    item_id: Annotated[
        uuid.UUID, Path(description="UUID идентификатор элемента обслуживания")
    ],
    maintenance_service: Annotated[MaintenanceService, Depends()],
):
    """
    Отметить деталь как обслуженную
    """
    # Проверяем, что элемент существует и принадлежит пользователю
    item = await maintenance_service.get_user_maintenance_item(item_id)
    if (
        not item
        or item.user_id != maintenance_service.user.id
        or item.vehicle_id != vehicle_id
    ):
        raise HTTPException(status_code=404, detail="Элемент обслуживания не найден")

    # Создаем запись об обслуживании
    today = date.today()

    # Получаем текущий пробег автомобиля
    vehicle = await maintenance_service.get_vehicle(vehicle_id)
    if not vehicle:
        raise HTTPException(status_code=404, detail="Автомобиль не найден")

    # Отмечаем деталь как обслуженную
    await maintenance_service.mark_item_as_serviced(
        item_id=item_id,
        service_date=today,
        service_odometer=vehicle.odometer,
    )

    # Перезагружаем страницу с обновленным списком
    maintenance_items, pagination = (
        await maintenance_service.get_items_requiring_service(
            vehicle_id=vehicle_id,
            page=1,  # После обновления возвращаемся на первую страницу
        )
    )

    pagination_params = PaginationParams(
        current_page=pagination["current_page"],
        total_pages=pagination["total_pages"],
        items_per_page=pagination["items_per_page"],
        total_items=pagination["total_items"],
    )

    # Возвращаем только обновленный список элементов, так как используется HTMX
    return templates.TemplateResponse(
        "maintenance_items_list.html",
        {
            "request": request,
            "vehicle": vehicle,
            "maintenance_items": maintenance_items,
            "pagination": pagination_params,
        },
    )


@router.get("/{vehicle_id}/add-maintenance-item", response_class=HTMLResponse)
async def add_maintenance_item_view(
    request: Request,
    vehicle_id: Annotated[uuid.UUID, Path(description="UUID идентификатор автомобиля")],
    maintenance_service: Annotated[MaintenanceService, Depends()],
):
    """
    Страница добавления новой детали для отслеживания
    """
    # Здесь будет форма для добавления новой детали
    # ...
    # Временная заглушка
    return templates.TemplateResponse(
        "maintenance_items_add.html",
        {
            "request": request,
            "user": maintenance_service.user,
            "vehicle_id": vehicle_id,
            "message": "Эта страница еще в разработке. Скоро здесь будет форма добавления деталей.",
        },
    )
