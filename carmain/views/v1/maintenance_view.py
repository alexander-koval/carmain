import json
from datetime import date, datetime
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
    MaintenanceCategory,
    UserMaintenanceItemUpdate,
)
from carmain.services.maintenance_service import MaintenanceService
from carmain.services.vehicle_service import VehicleService
from carmain.utils.maintenance_utils import (
    filter_maintenance_items_by_search,
    filter_maintenance_items_by_category,
    get_maintenance_item_icon,
)

router = APIRouter(prefix="/vehicles", tags=["maintenance"])


templates = Jinja2Templates(directory="carmain/templates")


def to_json_filter(value):
    if isinstance(value, uuid.UUID):
        return Markup(json.dumps(str(value)))
    return Markup(json.dumps(value))


templates.env.filters["tojson"] = to_json_filter


@router.get("/{vehicle_id}/maintenance")
async def maintenance_items_view(
    request: Request,
    vehicle_id: Annotated[uuid.UUID, Path(description="UUID идентификатор автомобиля")],
    maintenance_service: Annotated[MaintenanceService, Depends()],
    page: int = Query(1, ge=1),
    show_all: bool = False,
    q: Optional[str] = Query(None, description="Поисковый запрос"),
    category: Optional[MaintenanceCategory] = Query(
        None, description="Фильтр по категории"
    ),
):
    """
    Отображение деталей, требующих обслуживания для конкретного автомобиля
    """
    vehicle = await maintenance_service.get_vehicle(vehicle_id)
    if not vehicle or vehicle.user_id != maintenance_service.user.id:
        raise HTTPException(status_code=404, detail="Автомобиль не найден")

    user_vehicles = await maintenance_service.get_user_vehicles()

    maintenance_items, pagination = (
        await maintenance_service.get_items_requiring_service(
            vehicle_id=vehicle_id, page=page, page_size=10, show_all=show_all
        )
    )

    # Применяем фильтры
    maintenance_items = filter_maintenance_items_by_search(maintenance_items, q)
    maintenance_items = filter_maintenance_items_by_category(
        maintenance_items, category
    )

    pagination_params = PaginationParams(
        current_page=pagination["current_page"],
        total_pages=pagination["total_pages"],
        items_per_page=pagination["items_per_page"],
        total_items=pagination["total_items"],
    )

    is_htmx_request = request.headers.get("HX-Request") == "true"
    is_item_list_target = (
        is_htmx_request and request.headers.get("HX-Target") == "maintenance-items-list"
    )
    if is_item_list_target:
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


@router.patch("/{vehicle_id}/maintenance")
async def change_custom_interval(
    request: Request,
    vehicle_id: Annotated[uuid.UUID, Path(description="UUID идентификатор автомобиля")],
    maintenance_service: Annotated[MaintenanceService, Depends()],
    user_maintenance_item_update: UserMaintenanceItemUpdate = Depends(
        UserMaintenanceItemUpdate.as_form
    ),
):
    user_item = await maintenance_service.get_user_maintenance_item(
        user_maintenance_item_update.user_item_id
    )
    if (
        not user_item
        or user_item.vehicle_id != vehicle_id
        or user_item.user_id != maintenance_service.user.id
    ):
        raise HTTPException(status_code=404, detail="Элемент обслуживания не найден")

    await maintenance_service.update_user_maintenance_item(
        user_item.id, user_maintenance_item_update
    )

    maintenance_items, pagination = (
        await maintenance_service.get_items_requiring_service(
            vehicle_id=vehicle_id,
            page=1,
        )
    )

    pagination_params = PaginationParams(
        current_page=pagination["current_page"],
        total_pages=pagination["total_pages"],
        items_per_page=pagination["items_per_page"],
        total_items=pagination["total_items"],
    )

    return templates.TemplateResponse(
        "maintenance_items_list.html",
        {
            "request": request,
            "vehicle": user_item.vehicle,
            "maintenance_items": maintenance_items,
            "pagination": pagination_params,
            "today": date.today().isoformat(),
        },
    )


@router.post("/{vehicle_id}/maintenance")
async def mark_item_as_serviced(
    request: Request,
    vehicle_id: Annotated[uuid.UUID, Path(description="UUID идентификатор автомобиля")],
    maintenance_service: Annotated[MaintenanceService, Depends()],
    service_record_create: ServiceRecordCreate = Depends(ServiceRecordCreate.as_form),
):
    """
    Отметить деталь как обслуженную
    """
    item = await maintenance_service.mark_item_as_serviced(service_record_create)

    is_htmx = request.headers.get("HX-Request") == "true"
    is_service_records_container = (
        is_htmx and request.headers.get("HX-Target") == "service-records-container"
    )
    if is_service_records_container:
        records = await maintenance_service.get_service_records(item.id)
        sorted_records = sorted(records, key=lambda x: x.service_date, reverse=True)

        return templates.TemplateResponse(
            "service_records_list.html",
            {
                "request": request,
                "vehicle": item.vehicle,
                "item": item,
                "maintenance_item": item.maintenance_item,
                "records": sorted_records,
            },
        )

    maintenance_items, pagination = (
        await maintenance_service.get_items_requiring_service(
            vehicle_id=vehicle_id,
            page=1,
        )
    )

    pagination_params = PaginationParams(
        current_page=pagination["current_page"],
        total_pages=pagination["total_pages"],
        items_per_page=pagination["items_per_page"],
        total_items=pagination["total_items"],
    )

    return templates.TemplateResponse(
        "maintenance_items_list.html",
        {
            "request": request,
            "vehicle": item.vehicle,
            "maintenance_items": maintenance_items,
            "pagination": pagination_params,
        },
    )


@router.get("/{vehicle_id}/all-maintenance-items")
async def all_maintenance_items_view(
    request: Request,
    vehicle_id: Annotated[uuid.UUID, Path(description="UUID идентификатор автомобиля")],
    maintenance_service: Annotated[MaintenanceService, Depends()],
    q: Optional[str] = Query(None, description="Поисковый запрос"),
    category: Optional[MaintenanceCategory] = Query(
        None, description="Фильтр по категории"
    ),
    tracked_only: Optional[bool] = Query(
        False, description="Показывать только отслеживаемые"
    ),
):
    """
    Отображение справочника всех типов работ, с отметкой отслеживаемых пользователем
    """

    vehicle = await maintenance_service.get_vehicle(vehicle_id)
    if not vehicle or vehicle.user_id != maintenance_service.user.id:
        raise HTTPException(status_code=404, detail="Автомобиль не найден")

    all_items = await maintenance_service.get_maintenance_items(skip=0, limit=1000)

    user_items = await maintenance_service.get_user_maintenance_items(
        vehicle_id=vehicle_id, limit=1000
    )
    tracked_ids = {ui.item_id for ui in user_items}

    # Применяем фильтры
    filtered_items = filter_maintenance_items_by_search(all_items, q)
    filtered_items = filter_maintenance_items_by_category(filtered_items, category)

    items: List[Dict[str, Any]] = []
    for mi in filtered_items:
        is_tracked = mi.id in tracked_ids

        if tracked_only and not is_tracked:
            continue

        items.append(
            {
                "id": mi.id,
                "name": mi.name,
                "default_interval": mi.default_interval,
                "icon": get_maintenance_item_icon(mi.name),
                "is_tracked": is_tracked,
            }
        )

    is_htmx = request.headers.get("HX-Request") == "true"
    is_maintenance_container_target = (
        is_htmx and request.headers.get("HX-Target") == "maintenance-items-container"
    )
    context = {"request": request, "vehicle_id": vehicle_id, "maintenance_items": items}
    if is_maintenance_container_target:
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

    await maintenance_service.create_user_maintenance_item(
        {"item_id": item_id, "vehicle_id": vehicle_id}
    )

    mi = await maintenance_service.get_maintenance_item(item_id)
    if not mi:
        raise HTTPException(status_code=404, detail="Работа не найдена")
    item = {
        "id": mi.id,
        "name": mi.name,
        "default_interval": mi.default_interval,
        "icon": get_maintenance_item_icon(mi.name),
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
    umi = await maintenance_service.get_user_maintenance_item_by_item_id(item_id)
    if not umi or umi.vehicle_id != vehicle_id:
        raise HTTPException(status_code=404, detail="Элемент не отслеживается")
    await maintenance_service.delete_user_maintenance_item(umi.id)
    mi = await maintenance_service.get_maintenance_item(item_id)
    if not mi:
        raise HTTPException(status_code=404, detail="Работа не найдена")
    item = {
        "id": mi.id,
        "name": mi.name,
        "default_interval": mi.default_interval,
        "icon": get_maintenance_item_icon(mi.name),
        "is_tracked": False,
    }
    return templates.TemplateResponse(
        "maintenance_directory_card.html",
        {"request": request, "vehicle_id": vehicle_id, "item": item},
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

    # ...

    return templates.TemplateResponse(
        "maintenance_items_add.html",
        {
            "request": request,
            "user": maintenance_service.user,
            "vehicle_id": vehicle_id,
            "message": "Эта страница еще в разработке. Скоро здесь будет форма добавления деталей.",
        },
    )
