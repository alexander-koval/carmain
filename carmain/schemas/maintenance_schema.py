import uuid
from datetime import date, datetime
from enum import Enum
from typing import Optional, List

from pydantic import BaseModel, Field


class MaintenanceItemStatus(str, Enum):
    OVERDUE = "overdue"
    UPCOMING = "upcoming"
    NEVER_SERVICED = "never_serviced"
    OK = "ok"


class MaintenanceItemType(str, Enum):
    OIL_CHANGE = "oil_change"
    BRAKE_PADS = "brake_pads"
    TIMING_BELT = "timing_belt"
    AIR_FILTER = "air_filter"
    BATTERY = "battery"
    OTHER = "other"


class MaintenanceItemBase(BaseModel):
    name: str
    type: MaintenanceItemType
    default_interval: int = Field(..., description="Интервал обслуживания в километрах")


class MaintenanceItemCreate(MaintenanceItemBase):
    pass


class MaintenanceItemUpdate(BaseModel):
    name: Optional[str] = None
    type: Optional[MaintenanceItemType] = None
    default_interval: Optional[int] = None


class MaintenanceItem(MaintenanceItemBase):
    id: int

    class Config:
        orm_mode = True


class UserMaintenanceItemBase(BaseModel):
    vehicle_id: int
    item_id: int
    custom_interval: Optional[int] = None
    last_service_odometer: Optional[int] = None
    last_service_date: Optional[date] = None


class UserMaintenanceItemCreate(UserMaintenanceItemBase):
    pass


class UserMaintenanceItemUpdate(BaseModel):
    custom_interval: Optional[int] = None
    last_service_odometer: Optional[int] = None
    last_service_date: Optional[date] = None


class UserMaintenanceItem(UserMaintenanceItemBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True


class ServiceRecordBase(BaseModel):
    user_item_id: int
    service_date: date
    service_odometer: int
    comment: Optional[str] = None


class ServiceRecordCreate(ServiceRecordBase):
    pass


class ServiceRecordUpdate(BaseModel):
    service_date: Optional[date] = None
    service_odometer: Optional[int] = None
    comment: Optional[str] = None


class ServiceRecord(ServiceRecordBase):
    id: int
    created_at: datetime

    class Config:
        orm_mode = True


class MaintenanceItemDisplay(BaseModel):
    id: uuid.UUID
    name: str
    type: MaintenanceItemType
    status: MaintenanceItemStatus
    last_service_date: Optional[date] = None
    last_service_odometer: Optional[int] = None
    overdue_km: Optional[int] = None
    remaining_km: Optional[int] = None
    custom_interval: Optional[int] = None
    default_interval: int

    class Config:
        orm_mode = True


class PaginationParams(BaseModel):
    current_page: int = 1
    total_pages: int = 1
    items_per_page: int = 10
    total_items: int = 0


class MaintenanceItemsResponse(BaseModel):
    maintenance_items: List[MaintenanceItemDisplay]
    pagination: PaginationParams

    class Config:
        orm_mode = True
