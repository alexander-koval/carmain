from typing import Protocol, TypeVar

# Type definition for model
M = TypeVar("M")

# Type definition for Unique id
K = TypeVar("K")


class Repository(Protocol[K, M]):
    async def create(self, obj: M) -> M: ...

    async def delete_by_id(self, obj_id: K) -> M: ...

    async def get_by_id(self, obj_id: K) -> M: ...

    async def update_by_id(self, obj_id: K, obj: M) -> M: ...
