import uuid
from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from carmain.core.database import get_async_session
from carmain.models.vehicles import Vehicle
from carmain.repository.base_repository import BaseRepository


class VehicleRepository(BaseRepository[uuid.UUID, Vehicle]):

    def __init__(
        self, session: Annotated[AsyncSession, Depends(get_async_session)]
    ) -> None:
        super().__init__(Vehicle, session)
