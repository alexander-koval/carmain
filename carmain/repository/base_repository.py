from typing import Annotated, Optional, Any
from collections.abc import Sequence
from fastapi import Depends
from sqlalchemy import select, update, insert, delete, Row, RowMapping
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from carmain.core.database import get_async_session, Base
from carmain.core.exceptions import DuplicatedError, NotFoundError
from carmain.repository.repository import Repository, M, K


class BaseRepository(Repository[K, M]):
    def __init__(
        self, model: M, session: Annotated[AsyncSession, Depends(get_async_session)]
    ) -> None:
        self.model = model
        self.session = session

    async def get_by_id(
        self,
        obj_id: K,
        eager=False,
    ) -> M:
        query = select(self.model)
        # query = await self.session.query(self.model)
        if eager:
            for eager in getattr(self.model, "eagers", []):
                query = query.options(joinedload(getattr(M, eager)))
        query = query.where(self.model.id == obj_id)
        result = await self.session.scalar(query)
        if not result:
            raise NotFoundError(detail=f"not found id : {obj_id}")
        return result

    async def all(self) -> Sequence[M]:
        result = await self.session.scalars(select(self.model))
        return result.all()

    async def create(self, obj: M) -> M:
        try:
            self.session.add(obj)
            await self.session.commit()
            await self.session.refresh(obj)
        except IntegrityError as e:
            await self.session.rollback()
            raise DuplicatedError(detail=str(e.orig))
        return obj

    async def update_by_id(self, obj_id: K, update_payload: dict[str, Any]) -> M:
        db_obj = await self.session.get(self.model, obj_id)
        if not db_obj:
            raise NotFoundError(detail=f"not found id : {obj_id}")

        for key, value in update_payload.items():
            setattr(db_obj, key, value)

        try:
            await self.session.commit()
            await self.session.refresh(db_obj)
        except Exception:
            await self.session.rollback()
            raise
        return db_obj

    async def delete_by_id(self, obj_id: K) -> M:
        db_obj = await self.session.get(self.model, obj_id)
        if not db_obj:
            raise NotFoundError(detail=f"not found id: {obj_id}")
        try:
            await self.session.delete(db_obj)
            await self.session.commit()
        except Exception:
            await self.session.rollback()
            raise
        return db_obj
