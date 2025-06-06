import datetime
import uuid
from typing import Self, Optional

from pydantic import BaseModel, create_model, ConfigDict
from pydantic_partial import PartialModelMixin, create_partial_model


class VehicleSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    brand: str
    model: str
    year: int
    odometer: int


class VehicleCreate(VehicleSchema):
    user_id: int


class VehicleFind(PartialModelMixin, VehicleSchema):
    user_id: int


VehicleUpdate = create_partial_model(VehicleSchema)
