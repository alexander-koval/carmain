from sqladmin import ModelView
from carmain.models import vehicles


class VehicleAdmin(ModelView, model=vehicles.Vehicle):
    column_list = [
        vehicles.Vehicle.id,
        vehicles.Vehicle.brand,
        vehicles.Vehicle.model,
        vehicles.Vehicle.year,
    ]
