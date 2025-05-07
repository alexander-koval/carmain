import uuid
from typing import Annotated, Sequence
from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from carmain.core.database import get_async_session
from carmain.core.exceptions import NotFoundError
from carmain.models.records import ServiceRecord
from carmain.repository.base_repository import BaseRepository


class ServiceRecordRepository(BaseRepository):

    def __init__(self, session: Annotated[AsyncSession, Depends(get_async_session)]):
        super().__init__(ServiceRecord, session)

    async def get_by_user_item_id(
        self, item_id: uuid.UUID, skip=0, limit=10, eager=False
    ) -> Sequence[ServiceRecord]:
        query = select(self.model).where(ServiceRecord.user_item_id == item_id)
        if eager:
            for eager in getattr(self.model, "eagers", []):
                query = query.options(joinedload(getattr(self.model, eager)))
        result = await self.session.scalars(query)
        if not result:
            raise NotFoundError(detail=f"not found for user_item_id: {item_id}")
        return result.unique().all()
