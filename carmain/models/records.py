import datetime
import uuid

from sqlalchemy import Uuid, Integer, ForeignKey, String, DateTime, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy_utils import UUIDType
from carmain.core.database import Base


class ServiceRecord(Base):
    __tablename__ = "service_record"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_item_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType(binary=False),
        ForeignKey("user_maintenance_item.id"),
        default=lambda: uuid.uuid4().hex,
    )
    service_date: Mapped[datetime.datetime] = mapped_column(DateTime)
    service_odometer: Mapped[int] = mapped_column(Integer)
    comment: Mapped[str] = mapped_column(String(1024))
    user_maintenance_item = relationship(
        "UserMaintenanceItem", backref="service_records"
    )
