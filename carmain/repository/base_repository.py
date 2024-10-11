from typing import Annotated
from fastapi import Depends
from sqlalchemy import select, update, insert, delete
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from carmain.core.db import get_async_session, Base
from carmain.core.exceptions import DuplicatedError, NotFoundError


class BaseRepository:
    def __init__(
        self, model, session: Annotated[AsyncSession, Depends(get_async_session)]
    ) -> None:
        self.session = session
        self.model = model

    async def read_by_id(
        self,
        obj_id: int,
        eager=False,
    ):
        query = select(self.model)
        # query = await self.session.query(self.model)
        if eager:
            for eager in getattr(self.model, "eagers", []):
                query = query.options(joinedload(getattr(self.model, eager)))
        query = query.where(self.model.id == obj_id).first()
        if not query:
            raise NotFoundError(detail=f"not found id : {obj_id}")
        return self.session.execute(query)

    async def create(self, obj: Base):
        try:
            self.session.add(obj)
            await self.session.commit()
            # await session.refresh(query)
        except IntegrityError as e:
            raise DuplicatedError(detail=str(e.orig))
        return obj

    # async def update(self, obj_id: int, schema):
    #     await self.session.execute(
    #         update(schema.dict(exclude_none=True)).where(self.model.id == obj_id)
    #     )
    #     await self.session.commit()
    #     return self.read_by_id(obj_id)

    async def delete_by_id(self, obj_id: int):
        obj = await self.session.execute(
            delete(self.model).where(self.model.id == obj_id)
        )
        await self.session.commit()
        return obj

    # def update_attr(self, obj_id: int, column: str, value):
    #     with self.session_factory() as session:
    #         session.query(self.model).filter(self.model.id == obj_id).update(
    #             {column: value}
    #         )
    #         session.commit()
    #         return self.read_by_id(obj_id)
    #
    # def whole_update(self, obj_id: int, schema):
    #     with self.session_factory() as session:
    #         session.query(self.model).filter(self.model.id == obj_id).update(
    #             schema.dict()
    #         )
    #         session.commit()
    #         return self.read_by_id(obj_id)
    #
