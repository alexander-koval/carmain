from sqladmin import ModelView
from carmain.models.records import ServiceRecord


class ServiceRecordAdmin(ModelView, model=ServiceRecord):
    column_list = [ServiceRecord.id, "maintenance_item", "user"]

    @staticmethod
    def maintenance_item(obj):
        return obj.maintenance_item

    @staticmethod
    def user(obj):
        return obj.user
