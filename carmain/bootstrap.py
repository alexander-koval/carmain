from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from carmain.models.items import MaintenanceItem
from loguru import logger


async def create_initial_maintenance_items(session: AsyncSession):
    """
    Check existing MaintenanceItems and create initial
    :param session:
    :return:
    """
    result = await session.execute(select(MaintenanceItem))
    if result.scalars().first() is not None:
        logger.info("Maintenance Items exists. Skip creating.")
        return

    logger.info("Creating Maintenance Items...")

    maintenance_items = [
        MaintenanceItem(name="Трансмиссионное масло", default_interval=80000),
        MaintenanceItem(name="Жидкость ГУР", default_interval=120000),
        MaintenanceItem(name="Масло редуктора", default_interval=75000),
        MaintenanceItem(name="Масляный фильтр", default_interval=6000),
        MaintenanceItem(name="Топливный фильтр", default_interval=25000),
        MaintenanceItem(name="Воздушный фильтр", default_interval=6000),
        MaintenanceItem(name="Ремень ГРМ", default_interval=100000),
        MaintenanceItem(name="Антифриз", default_interval=60000),
        MaintenanceItem(name="Тосол", default_interval=60000),
        MaintenanceItem(name="Тормозная жидкость", default_interval=57000),
        MaintenanceItem(name="Свечи", default_interval=18000),
        MaintenanceItem(name="Тормозные колодки", default_interval=15000),
        MaintenanceItem(name="Тормозные диски", default_interval=30000),
        MaintenanceItem(name="Тормозные барабаны", default_interval=15000),
        MaintenanceItem(name="Масло моторное", default_interval=6000),
    ]
    session.add_all(maintenance_items)
    await session.commit()
    logger.info("Maintenance Items Created...")
