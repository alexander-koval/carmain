import datetime
import uuid

from sqlalchemy import Uuid, Integer, ForeignKey, String, Date
from sqlalchemy.orm import Mapped, mapped_column
from carmain.core.database import Base


class Vehicle(Base):
    """Vehicle table definition"""

    __tablename__ = "vehicle"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("user.id"))
    brand: Mapped[str] = mapped_column(String(64))
    model: Mapped[str] = mapped_column(String(256))
    year: Mapped[datetime.date] = mapped_column(Date)
    odometer: Mapped[int] = mapped_column(Integer)
