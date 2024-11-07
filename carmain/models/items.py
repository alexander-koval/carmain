import datetime
import uuid

from sqlalchemy import Uuid, Integer, ForeignKey, String, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from carmain.core.database import Base


class MaintenanceItem(Base):
    __tablename__ = "maintenance_item"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, index=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(128))
    default_interval: Mapped[int] = mapped_column(Integer)


class UserMaintenanceItem(Base):
    __tablename__ = "user_maintenance_item"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, index=True, default=uuid.uuid4
    )
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("user.id"))
    item_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("maintenance_item.id"))
    vehicle_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("vehicle.id"))
    custom_interval: Mapped[int] = mapped_column(Integer, nullable=True)
    last_service_odometer: Mapped[int] = mapped_column(Integer, nullable=True)
    last_service_date: Mapped[datetime.datetime] = mapped_column(
        DateTime, nullable=True
    )
