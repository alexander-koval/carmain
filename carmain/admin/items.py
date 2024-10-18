from sqladmin import ModelView
from carmain.models import items


class MaintenanceItemAdmin(ModelView, model=items.MaintenanceItem):
    column_list = [items.MaintenanceItem.id]


class UserMaintenanceItemAdmin(ModelView, model=items.UserMaintenanceItem):
    column_list = [items.UserMaintenanceItem.id]
