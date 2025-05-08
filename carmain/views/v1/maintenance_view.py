import json
from datetime import date
import uuid
from typing import Optional, List, Dict, Any, Annotated

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Request,
    Query,
    Path,
    Form,
    File,
    UploadFile,
)
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from markupsafe import Markup
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


def to_json_filter(value):
    if isinstance(value, uuid.UUID):
        return Markup(json.dumps(str(value)))
    return Markup(json.dumps(value))


templates.env.filters["tojson"] = to_json_filter

# Используем инъекцию зависимостей напрямую через MaintenanceService


@router.get("/{vehicle_id}/maintenance")
async def maintenance_items_view(
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
                "today": date.today().isoformat(),
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
            "today": date.today().isoformat(),
        },
    )


@router.get("/{vehicle_id}/all-maintenance-items")
async def all_maintenance_items_view(
    request: Request,
    vehicle_id: Annotated[uuid.UUID, Path(description="UUID идентификатор автомобиля")],
    maintenance_service: Annotated[MaintenanceService, Depends()],
    q: Optional[str] = Query(None, description="Поисковый запрос"),
    tracked_only: Optional[bool] = Query(
        False, description="Показывать только отслеживаемые"
    ),
):
    """
    Отображение справочника всех типов работ, с отметкой отслеживаемых пользователем
    """
    # Проверяем право доступа к автомобилю
    vehicle = await maintenance_service.get_vehicle(vehicle_id)
    if not vehicle or vehicle.user_id != maintenance_service.user.id:
        raise HTTPException(status_code=404, detail="Автомобиль не найден")

    # Получаем все типы работ
    all_items = await maintenance_service.get_maintenance_items(skip=0, limit=1000)
    # Получаем отмеченные пользователем для данного автомобиля
    user_items = await maintenance_service.get_user_maintenance_items(
        vehicle_id=vehicle_id, limit=1000
    )
    tracked_ids = {ui.item_id for ui in user_items}

    # Формируем список элементов для отображения
    items: List[Dict[str, Any]] = []
    for mi in all_items:
        # Простейшая фильтрация по поиску
        if q and q.lower() not in mi.name.lower():
            continue
        is_tracked = mi.id in tracked_ids
        # Фильтрация по отслеживаемым
        if tracked_only and not is_tracked:
            continue
        # Определяем иконку исходя из названия
        name_lower = mi.name.lower()
        if "масл" in name_lower or "oil" in name_lower:
            icon = "oil-can"
        elif "тормоз" in name_lower or "brake" in name_lower:
            icon = "exclamation-circle"
        elif "ремень" in name_lower or "грм" in name_lower:
            icon = "cogs"
        elif "фильтр" in name_lower or "filter" in name_lower:
            icon = "filter"
        elif "аккум" in name_lower or "battery" in name_lower:
            icon = "car-battery"
        else:
            icon = "wrench"
        items.append(
            {
                "id": mi.id,
                "name": mi.name,
                "default_interval": mi.default_interval,
                "icon": icon,
                "is_tracked": is_tracked,
            }
        )

    # Проверяем HTMX запрос
    is_htmx = request.headers.get("HX-Request") == "true"
    context = {"request": request, "vehicle_id": vehicle_id, "maintenance_items": items}
    if is_htmx:
        return templates.TemplateResponse("maintenance_directory_list.html", context)
    return templates.TemplateResponse("maintenance_directory.html", context)


@router.post("/{vehicle_id}/maintenance-items/{item_id}/track")
async def track_maintenance_item(
    request: Request,
    vehicle_id: Annotated[uuid.UUID, Path(description="UUID идентификатор автомобиля")],
    item_id: Annotated[
        uuid.UUID, Path(description="UUID идентификатор элемента обслуживания")
    ],
    maintenance_service: Annotated[MaintenanceService, Depends()],
):
    """
    Добавить работу в отслеживаемые пользователем для данного автомобиля
    """
    vehicle = await maintenance_service.get_vehicle(vehicle_id)
    if not vehicle or vehicle.user_id != maintenance_service.user.id:
        raise HTTPException(status_code=404, detail="Автомобиль не найден")
    # Создаем связь UserMaintenanceItem
    await maintenance_service.create_user_maintenance_item(
        {"item_id": item_id, "vehicle_id": vehicle_id}
    )
    # Загружаем данные по работе
    mi = await maintenance_service.get_maintenance_item(item_id)
    if not mi:
        raise HTTPException(status_code=404, detail="Работа не найдена")
    name_lower = mi.name.lower()
    if "масл" in name_lower or "oil" in name_lower:
        icon = "oil-can"
    elif "тормоз" in name_lower or "brake" in name_lower:
        icon = "exclamation-circle"
    elif "ремень" in name_lower or "грм" in name_lower:
        icon = "cogs"
    elif "фильтр" in name_lower or "filter" in name_lower:
        icon = "filter"
    elif "аккум" in name_lower or "battery" in name_lower:
        icon = "car-battery"
    else:
        icon = "wrench"
    item = {
        "id": mi.id,
        "name": mi.name,
        "default_interval": mi.default_interval,
        "icon": icon,
        "is_tracked": True,
    }
    return templates.TemplateResponse(
        "maintenance_directory_card.html",
        {"request": request, "vehicle_id": vehicle_id, "item": item},
    )


@router.post(
    "/{vehicle_id}/maintenance-items/{item_id}/untrack", response_class=HTMLResponse
)
async def untrack_maintenance_item(
    request: Request,
    vehicle_id: Annotated[uuid.UUID, Path(description="UUID идентификатор автомобиля")],
    item_id: Annotated[
        uuid.UUID, Path(description="UUID идентификатор элемента обслуживания")
    ],
    maintenance_service: Annotated[MaintenanceService, Depends()],
):
    """
    Убрать работу из отслеживаемых пользователем для данного автомобиля
    """
    vehicle = await maintenance_service.get_vehicle(vehicle_id)
    if not vehicle or vehicle.user_id != maintenance_service.user.id:
        raise HTTPException(status_code=404, detail="Автомобиль не найден")
    umi = await maintenance_service.get_user_maintenance_item(item_id)
    if not umi or umi.vehicle_id != vehicle_id:
        raise HTTPException(status_code=404, detail="Элемент не отслеживается")
    await maintenance_service.delete_user_maintenance_item(item_id)
    mi = await maintenance_service.get_maintenance_item(item_id)
    if not mi:
        raise HTTPException(status_code=404, detail="Работа не найдена")
    name_lower = mi.name.lower()
    if "масл" in name_lower or "oil" in name_lower:
        icon = "oil-can"
    elif "тормоз" in name_lower or "brake" in name_lower:
        icon = "exclamation-circle"
    elif "ремень" in name_lower or "грм" in name_lower:
        icon = "cogs"
    elif "фильтр" in name_lower or "filter" in name_lower:
        icon = "filter"
    elif "аккум" in name_lower or "battery" in name_lower:
        icon = "car-battery"
    else:
        icon = "wrench"
    item = {
        "id": mi.id,
        "name": mi.name,
        "default_interval": mi.default_interval,
        "icon": icon,
        "is_tracked": False,
    }
    return templates.TemplateResponse(
        "maintenance_directory_card.html",
        {"request": request, "vehicle_id": vehicle_id, "item": item},
    )


@router.post("/{vehicle_id}/maintenance-items/{item_id}/service")
async def mark_item_as_serviced(
    request: Request,
    vehicle_id: Annotated[uuid.UUID, Path(description="UUID идентификатор автомобиля")],
    item_id: Annotated[
        uuid.UUID, Path(description="UUID идентификатор элемента обслуживания")
    ],
    maintenance_service: Annotated[MaintenanceService, Depends()],
    service_date: Optional[str] = Form(None),
    service_odometer: Optional[int] = Form(None),
    service_comment: Optional[str] = Form(None),
    service_photo: Optional[UploadFile] = File(None),
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

    # Обрабатываем дату обслуживания
    service_date_obj = None
    if service_date:
        try:
            service_date_obj = date.fromisoformat(service_date)
        except ValueError:
            service_date_obj = date.today()
    else:
        service_date_obj = date.today()

    # Получаем текущий пробег автомобиля если не указан другой
    if not service_odometer:
        vehicle = await maintenance_service.get_vehicle(vehicle_id)
        if not vehicle:
            raise HTTPException(status_code=404, detail="Автомобиль не найден")
        service_odometer = vehicle.odometer

    photo_path = None
    if service_photo:
        try:
            pass
        except Exception as e:
            pass

    # Отмечаем деталь как обслуженную
    await maintenance_service.mark_item_as_serviced(
        item_id=item_id,
        service_date=service_date_obj,
        service_odometer=service_odometer,
        comment=service_comment,
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


@router.get("/{vehicle_id}/add-maintenance-item")
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
