import datetime
import uuid

from pydantic import BaseModel
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
