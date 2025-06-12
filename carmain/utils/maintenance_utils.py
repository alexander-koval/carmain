from typing import List, Optional, Union
from carmain.schemas.maintenance_schema import MaintenanceCategory, MaintenanceItemDisplay, MaintenanceItemType
from carmain.models.items import MaintenanceItem


def filter_maintenance_items_by_search(
    items: List[Union[MaintenanceItemDisplay, MaintenanceItem]], 
    search_query: Optional[str]
) -> List[Union[MaintenanceItemDisplay, MaintenanceItem]]:
    """Фильтрация элементов обслуживания по поисковому запросу"""
    if not search_query:
        return items
    
    query_lower = search_query.lower()
    return [item for item in items if query_lower in item.name.lower()]


def filter_maintenance_items_by_category(
    items: List[Union[MaintenanceItemDisplay, MaintenanceItem]], 
    category: Optional[MaintenanceCategory]
) -> List[Union[MaintenanceItemDisplay, MaintenanceItem]]:
    """Фильтрация элементов обслуживания по категории"""
    if not category or category == MaintenanceCategory.ALL:
        return items
    
    filtered_items = []
    for item in items:
        if _item_matches_category(item.name, category):
            filtered_items.append(item)
    
    return filtered_items


def _item_matches_category(item_name: str, category: MaintenanceCategory) -> bool:
    """Проверяет, соответствует ли элемент указанной категории"""
    name_lower = item_name.lower()
    
    if category == MaintenanceCategory.ENGINE:
        return "масл" in name_lower or "двигател" in name_lower
    elif category == MaintenanceCategory.BRAKES:
        return "тормоз" in name_lower or "колод" in name_lower
    elif category == MaintenanceCategory.FILTERS:
        return "фильтр" in name_lower
    elif category == MaintenanceCategory.BATTERY:
        return "аккум" in name_lower or "батар" in name_lower
    
    return False


def get_maintenance_item_icon(item_name: str) -> str:
    """Возвращает иконку для элемента обслуживания на основе названия"""
    name_lower = item_name.lower()
    
    if "масл" in name_lower or "oil" in name_lower:
        return "oil-can"
    elif "тормоз" in name_lower or "brake" in name_lower:
        return "exclamation-circle"
    elif "ремень" in name_lower or "грм" in name_lower:
        return "cogs"
    elif "фильтр" in name_lower or "filter" in name_lower:
        return "filter"
    elif "аккум" in name_lower or "battery" in name_lower:
        return "car-battery"
    else:
        return "wrench"


def get_maintenance_item_type(item_name: str) -> MaintenanceItemType:
    """Возвращает тип элемента обслуживания на основе названия"""
    name_lower = item_name.lower()
    
    if "масл" in name_lower:
        return MaintenanceItemType.OIL_CHANGE
    elif "тормоз" in name_lower or "колод" in name_lower:
        return MaintenanceItemType.BRAKE_PADS
    elif "ремен" in name_lower or "грм" in name_lower:
        return MaintenanceItemType.TIMING_BELT
    elif "фильтр" in name_lower and ("воздух" in name_lower or "воздуш" in name_lower):
        return MaintenanceItemType.AIR_FILTER
    elif "аккумулятор" in name_lower or "батар" in name_lower:
        return MaintenanceItemType.BATTERY
    else:
        return MaintenanceItemType.OTHER