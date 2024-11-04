from typing import Protocol, TypeVar

from carmain.models.users import User
from carmain.repository.base_repository import BaseRepository

# Type definition for schema
S = TypeVar("S")

# Type definition for model
M = TypeVar("M")

# Type definition for Unique id
K = TypeVar("K")


class BaseService(Protocol[K, S, M]):
    async def get_by_id(self, obj_id: K) -> M: ...

    async def add(self, schema: S) -> M: ...

    async def patch(self, obj_id: K, schema: S) -> M: ...

    async def remove_by_id(self, obj_id: K) -> M: ...

    async def all(self) -> list[M]: ...
