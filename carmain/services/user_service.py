from typing import Sequence

from carmain.models.users import User
from carmain.repository.user_repository import UserRepository
from carmain.schemas.user_schema import UserSchema
from carmain.services.base_service import BaseService, M, K


class UserService(BaseService[int, UserSchema, User]):
    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository

    async def get_by_id(self, obj_id: int) -> User:
        return await self.user_repository.get_by_id(obj_id)

    async def add(self, schema: UserSchema) -> User:
        data = schema.model_dump(exclude_unset=True, exclude_none=True)
        user = User(**data)
        return await self.user_repository.create(user)

    async def patch(self, obj_id: int, schema: UserSchema) -> User:
        update_data = schema.model_dump(
            exclude_unset=True, exclude_defaults=True, exclude_none=True
        )
        return await self.user_repository.update_by_id(obj_id, update_data)

    async def remove_by_id(self, obj_id: int) -> User:
        return await self.user_repository.delete_by_id(obj_id)

    async def all(self) -> Sequence[User]:
        return await self.user_repository.all()
