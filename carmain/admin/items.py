from sqladmin import ModelView
from carmain.models import items


class MaintenanceItemAdmin(ModelView, model=items.MaintenanceItem):
    column_default_sort = "name"
    column_list = [items.MaintenanceItem.name, items.MaintenanceItem.default_interval]


class UserMaintenanceItemAdmin(ModelView, model=items.UserMaintenanceItem):
    column_list = [items.UserMaintenanceItem.id, "maintenance_item", "vehicle", "user"]

    @staticmethod
    def maintenance_item(obj):
        return obj.maintenance_item

    @staticmethod
    def vehicle(obj):
        return obj.vehicle

    @staticmethod
    def user(obj):
        return obj.user
