from carmain.models.users import User
from carmain.repository.user_repository import UserRepository
from carmain.services.base_service import BaseService, M, K


class UserService(BaseService[int, User]):
    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository

    async def get_by_id(self, obj_id: int) -> User:
        return User()

    async def add(self, obj: User) -> User:
        return User()

    async def patch(self, obj_id: int, obj: User) -> User:
        return User()

    async def remove_by_id(self, obj_id: int) -> User:
        return User()

    async def all(self) -> list[User]:
        return []
