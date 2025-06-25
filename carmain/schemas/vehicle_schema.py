import datetime
import uuid
from typing import Self, Optional, Annotated

from fastapi import UploadFile, File, Form
from pydantic import BaseModel, create_model, ConfigDict
from pydantic_partial import PartialModelMixin, create_partial_model


class VehicleSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    brand: str
    model: str
    year: int
    odometer: int
    photo: Optional[str] = None


class VehicleCreate(VehicleSchema):
    user_id: int


class VehicleFind(PartialModelMixin, VehicleSchema):
    user_id: int


class VehicleUpdate(PartialModelMixin, VehicleSchema):

    @classmethod
    def as_form(
        cls,
        brand: Annotated[str, Form()],
        model: Annotated[str, Form()],
        year: Annotated[int, Form()],
        odometer: Annotated[int, Form()],
    ):
        return cls(
            brand=brand,
            model=model,
            year=year,
            odometer=odometer,
        )
