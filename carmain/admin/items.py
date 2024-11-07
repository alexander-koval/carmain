from sqladmin import ModelView
from carmain.models import items


class MaintenanceItemAdmin(ModelView, model=items.MaintenanceItem):
    column_default_sort = "name"
    column_list = [items.MaintenanceItem.name, items.MaintenanceItem.default_interval]


class UserMaintenanceItemAdmin(ModelView, model=items.UserMaintenanceItem):
    column_list = [items.UserMaintenanceItem.id]
