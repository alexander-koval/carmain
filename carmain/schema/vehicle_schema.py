import datetime
import uuid
from typing import Self, Optional

from pydantic import BaseModel, create_model
from pydantic_partial import PartialModelMixin, create_partial_model


class VehicleSchema(BaseModel):
    brand: str
    model: str
    year: datetime.date
    odometer: int


class VehicleCreate(VehicleSchema):
    user_id: int


class VehicleFind(PartialModelMixin, VehicleSchema):
    user_id: int


VehicleUpdate = create_partial_model(VehicleSchema)
