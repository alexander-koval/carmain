from sqladmin import ModelView
from carmain.models.records import ServiceRecord


class ServiceRecordAdmin(ModelView, model=ServiceRecord):
    column_list = [ServiceRecord.id, "maintenance_item_name", "vehicle", "user", "service_date", "service_odometer"]
    
    # Определяем столбцы для фильтрации
    column_filters = [ServiceRecord.service_date, ServiceRecord.service_odometer]
    
    # Определяем поля поиска
    column_searchable_list = []

    @staticmethod
    def maintenance_item_name(obj):
        """Получить название элемента обслуживания"""
        if obj.user_maintenance_item and obj.user_maintenance_item.maintenance_item:
            return obj.user_maintenance_item.maintenance_item.name
        return "Нет данных"

    @staticmethod
    def vehicle(obj):
        """Получить информацию об автомобиле"""
        if obj.user_maintenance_item and obj.user_maintenance_item.vehicle:
            return f"{obj.user_maintenance_item.vehicle.brand} {obj.user_maintenance_item.vehicle.model}"
        return "Нет данных"

    @staticmethod
    def user(obj):
        """Получить информацию о пользователе"""
        if obj.user_maintenance_item and obj.user_maintenance_item.user:
            return obj.user_maintenance_item.user.email
        return "Нет данных"
