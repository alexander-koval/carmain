import datetime
import uuid

from sqlalchemy import Uuid, Integer, ForeignKey, String, Date, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from carmain.core.database import Base
from carmain.models.users import User


class Vehicle(Base):
    """Vehicle table definition"""

    __tablename__ = "vehicle"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, index=True, default=uuid.uuid4
    )
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("user.id"))
    brand: Mapped[str] = mapped_column(String(64))
    model: Mapped[str] = mapped_column(String(256))
    year: Mapped[datetime.date] = mapped_column(Date)
    odometer: Mapped[int] = mapped_column(Integer)
    user: Mapped[User] = relationship(back_populates="vehicles")
    maintenance_items: Mapped[list["UserMaintenanceItem"]] = relationship(back_populates="vehicle")

    def __str__(self):
        return f"{self.brand} {self.model}"
