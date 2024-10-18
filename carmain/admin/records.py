from sqladmin import ModelView
from carmain.models.records import ServiceRecord


class ServiceRecordAdmin(ModelView, model=ServiceRecord):
    column_list = [ServiceRecord.id]
