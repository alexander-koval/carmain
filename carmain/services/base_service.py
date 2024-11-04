from typing import Protocol, TypeVar

from carmain.models.users import User
from carmain.repository.base_repository import BaseRepository

# Type definition for schema
S = TypeVar("S")

# Type definition for model
M = TypeVar("M")

# Type definition for Unique id
K = TypeVar("K")


class BaseService(Protocol[K, S]):
    async def get_by_id(self, obj_id: K) -> S: ...

    async def add(self, schema: S) -> S: ...

    async def patch(self, obj_id: K, schema: S) -> S: ...

    async def remove_by_id(self, obj_id: K) -> S: ...

    async def all(self) -> list[S]: ...
