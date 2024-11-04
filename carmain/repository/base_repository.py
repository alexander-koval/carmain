from typing import Annotated
from fastapi import Depends
from sqlalchemy import select, update, insert, delete
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

    async def all(self) -> list[M]:
        return await self.session.scalars(select(self.model))

    async def create(self, obj: M) -> M:
        try:
            self.session.add(obj)
            await self.session.commit()
            # await session.refresh(query)
        except IntegrityError as e:
            raise DuplicatedError(detail=str(e.orig))
        return obj

    async def update_by_id(self, obj_id: K, schema) -> M:
        await self.session.execute(
            update(self.model)
            .where(self.model.id == obj_id)
            .values(
                schema.model_dump(
                    exclude_none=True, exclude_unset=True, exclude_defaults=True
                )
            )
        )
        await self.session.commit()
        return await self.get_by_id(obj_id)

    async def delete_by_id(self, obj_id: K) -> M:
        obj = await self.session.scalar(
            select(self.model).where(self.model.id == obj_id)
        )
        await self.session.delete(obj)
        await self.session.commit()
        return obj
