import json
from datetime import date, datetime
import uuid
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Request, Path
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from markupsafe import Markup

from carmain.models.items import UserMaintenanceItem
from carmain.models.vehicles import Vehicle
from carmain.schemas.maintenance_schema import ServiceRecordUpdate, ServiceRecordCreate
from carmain.services.maintenance_service import MaintenanceService

router = APIRouter(prefix="/service-records", tags=["service-records"])

templates = Jinja2Templates(directory="carmain/templates")


def to_json_filter(value: Any) -> Any:
    if isinstance(value, uuid.UUID):
        return Markup(json.dumps(str(value)))
    return Markup(json.dumps(value))


templates.env.filters["tojson"] = to_json_filter


@router.get("/{item_id}")
async def service_record_history_view(
    request: Request,
    item_id: Annotated[
        uuid.UUID, Path(description="UUID идентификатор элемента обслуживания")
    ],
    maintenance_service: Annotated[MaintenanceService, Depends()],
):
    """
    Отображение истории обслуживания для конкретной детали
    """
    item = await maintenance_service.get_user_maintenance_item(item_id)
    if not item or item.user_id != maintenance_service.user.id:
        raise HTTPException(status_code=404, detail="Элемент обслуживания не найден")

    records = await maintenance_service.get_service_records(item_id)

    name_lower = item.maintenance_item.name.lower()
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

    sorted_records = sorted(records, key=lambda x: x.service_date, reverse=True)

    today = date.today().isoformat()

    return templates.TemplateResponse(
        "service_records.html",
        {
            "request": request,
            "user": maintenance_service.user,
            "vehicle": item.vehicle,
            "item": item,
            "maintenance_item": item.maintenance_item,
            "records": sorted_records,
            "icon": icon,
            "today": today,
        },
    )


@router.patch(
    "/{item_id}",
    response_class=HTMLResponse,
)
async def update_service_record(
    request: Request,
    item_id: Annotated[
        uuid.UUID, Path(description="UUID идентификатор элемента обслуживания")
    ],
    service_record_update: Annotated[
        ServiceRecordUpdate,
        Depends(ServiceRecordUpdate.as_form),
    ],
    maintenance_service: Annotated[MaintenanceService, Depends()],
):
    """
    Обновить запись об обслуживании автомобиля и вернуть обновленный список записей.
    """
    updated_record = await maintenance_service.update_service_record(
        service_record_update.record_id, service_record_update
    )

    user_item_id = item_id
    item = await maintenance_service.get_user_maintenance_item(user_item_id)
    if not item or item.user_id != maintenance_service.user.id:
        raise HTTPException(status_code=404, detail="Элемент обслуживания не найден")

    records = await maintenance_service.get_service_records(user_item_id)
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


@router.post(
    "/{item_id}",
    response_class=HTMLResponse,
)
async def create_service_record(
    request: Request,
    item_id: Annotated[
        uuid.UUID, Path(description="UUID идентификатор элемента обслуживания")
    ],
    service_record_create: Annotated[
        ServiceRecordCreate,
        Depends(ServiceRecordCreate.as_form),
    ],
    maintenance_service: Annotated[MaintenanceService, Depends()],
):
    """
    Обновить запись об обслуживании автомобиля и вернуть обновленный список записей.
    """
    _ = await maintenance_service.create_service_record(service_record_create)

    user_item_id = item_id
    item: UserMaintenanceItem = await maintenance_service.get_user_maintenance_item(
        user_item_id
    )
    if not item or item.user_id != maintenance_service.user.id:
        raise HTTPException(status_code=404, detail="Элемент обслуживания не найден")

    vehicle = item.vehicle
    if not vehicle or vehicle.user_id != maintenance_service.user.id:
        raise HTTPException(status_code=404, detail="Автомобиль не найден")

    records = await maintenance_service.get_service_records(user_item_id)
    sorted_records = sorted(records, key=lambda x: x.service_date, reverse=True)

    is_htmx_request = request.headers.get("HX-Request") == "true"
    is_item_list_target = (
        is_htmx_request and request.headers.get("HX-Target") == "maintenance-items-list"
    )

    # if is_item_list_target:
    #     return templates.TemplateResponse(
    #         "maintenance_items_list.html",
    #         {
    #             "request": request,
    #             "vehicle": vehicle,
    #             "maintenance_items": maintenance_items,
    #             "pagination": pagination_params,
    #             "today": date.today().isoformat(),
    #         },
    #     )
    #
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
